"""Free offline neural speech. Model files are bundled, never fetched at runtime."""
import hashlib
import json
import os
from pathlib import Path
import queue
import sys
import threading
import time
import wave
import array

VOICES={'Bill — English (male, Pocket TTS)':('pt_bill','en'),
        'Peter — English (male, Pocket TTS)':('pt_peter','en'),
        'Michael — English (male, Pocket TTS)':('pt_michael','en'),
        'Michael — American English (male)':('am_michael','en-us'),
        'George — British English (male)':('bm_george','en-gb')}
DEFAULT_VOICE='pt_bill'


def language(voice):
    return next((lang for code,lang in VOICES.values() if code==voice),'en-us')


class NeuralVoice:
    def __init__(self,assets,cache):
        self.assets=Path(assets);self.cache=Path(cache);self.events=queue.Queue()
        self.output=None;self.model=None;self.super_model=None;self.pocket_model=None;self.error=None;self.loading=False;self.lock=threading.Lock()

    def load(self,voice=DEFAULT_VOICE):
        ready=self.pocket_model if voice.startswith('pt_') else self.super_model if voice.startswith('st3_') else self.model
        if ready or self.loading:return
        self.loading=True
        def run():
            try:
                with self.lock:
                    if voice.startswith('pt_'):self._ensure_pocket_model()
                    elif voice.startswith('st3_'):self._ensure_super_model()
                    else:self._ensure_model()
                self.events.put(('ready','Free neural voices ready. No API key or internet needed.'))
            except Exception as exc:
                self.error=str(exc);self.events.put(('error','Free voice could not load. Use the complete updated EXE.'))
            finally:self.loading=False
        threading.Thread(target=run,daemon=True).start()

    def _ensure_pocket_model(self):
        if self.pocket_model:return
        from .pocket_voice import PocketVoice
        model=PocketVoice(self.assets/'pocket');model.load();self.pocket_model=model

    def _ensure_super_model(self):
        if self.super_model:return
        from .supertonic_voice import SupertonicVoice
        model=SupertonicVoice(self.assets/'supertonic');model.load();self.super_model=model

    def _ensure_model(self):
        # Keep CPU use bounded while iRacing is running.
        if self.model:return
        # Official ORT privacy control: must precede the first runtime import.
        # Prevents the uploader, initialization events and device ID creation.
        os.environ['ORT_DISABLE_TELEMETRY']='1'
        import onnxruntime as ort
        ort.disable_telemetry_events()
        from kokoro_onnx import Kokoro
        options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
        options.log_severity_level=3
        session=ort.InferenceSession(str(self.assets/'kokoro-v1.0.int8.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
        self.model=Kokoro.from_session(session,str(self.assets/'voices-v1.0.bin'))

    def render(self,text,voice=DEFAULT_VOICE,speed=1.05):
        if voice not in {v[0] for v in VOICES.values()}:raise ValueError('Unknown free voice.')
        if not .8<=speed<=1.5:raise ValueError('Speech speed outside supported range.')
        text=str(text).strip()[:1600]
        if not text:raise ValueError('Empty speech.')
        self.cache.mkdir(parents=True,exist_ok=True)
        key=hashlib.sha256((voice+'|'+str(speed)+'|'+text).encode()).hexdigest()
        path=self.cache/(key+'.wav')
        if path.exists():
            try:
                with wave.open(str(path),'rb') as f:audio=array.array('h',f.readframes(f.getnframes()))
                if audio and max(map(abs,audio))>60:return path
            except (OSError,wave.Error,EOFError):pass
            path.unlink(missing_ok=True)
        with self.lock:
            if voice.startswith('pt_'):
                self._ensure_pocket_model()
                temporary=path.with_suffix('.part.wav')
                self.pocket_model.write(text,voice,temporary)
                temporary.replace(path)
                return path
            import numpy as np
            if voice.startswith('st3_'):
                self._ensure_super_model();audio,rate=self.super_model.create(text,voice[-2:].upper(),speed)
            else:
                self._ensure_model();audio,rate=self.model.create(text,voice=voice,speed=speed,lang=language(voice))
            temporary=path.with_suffix('.tmp')
            with wave.open(str(temporary),'wb') as f:
                f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate)
                f.writeframes((np.clip(audio,-1,1)*32767).astype('<i2').tobytes())
            temporary.replace(path)
        return path

    def clips(self,voice):return self.assets/'clips'/voice

    def play(self,path):
        if self.output is not None:
            if not self.output.play(path):raise OSError('Audio output is not ready')
            return
        if sys.platform!='win32':return
        import winsound
        winsound.PlaySound(str(path),winsound.SND_FILENAME|winsound.SND_ASYNC|winsound.SND_NODEFAULT)

    @staticmethod
    def duration(path):
        with wave.open(str(path),'rb') as f:return f.getnframes()/f.getframerate()

    def stop(self):
        if self.pocket_model:self.pocket_model.stop()
        if self.output is not None:self.output.stop();return
        if sys.platform=='win32':
            import winsound
            winsound.PlaySound(None,0)
