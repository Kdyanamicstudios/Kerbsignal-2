"""Cache short Windows SAPI WAV clips, then play without per-call TTS startup."""
import base64
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import wave

from .cues import PHRASES
from .spotter import TRAFFIC_PHRASES
AUDIO_PHRASES={**PHRASES,**{'traffic_'+k:v for k,v in TRAFFIC_PHRASES.items()}}


class CueAudio:
    def __init__(self,folder,voice_id="",bundled_clips=None,output=None):
        self.output=output
        self.folder=Path(folder);self.voice_id=voice_id;self.ready=False;self.preparing=False
        self.events=queue.Queue();self.durations={};self.until=0.
        self.bundled_clips=Path(bundled_clips) if bundled_clips else None

    @property
    def busy(self):return time.monotonic()<self.until

    def prepare(self):
        if self.ready or self.preparing:return
        if self.bundled_clips:
            try:
                for key in AUDIO_PHRASES:
                    with wave.open(str(self.bundled_clips/(key+'.wav')),'rb') as f:
                        duration=f.getnframes()/f.getframerate()
                    if not .05<duration<4.5:raise ValueError('Invalid bundled driving cue.')
                    self.durations[key]=duration
                self.folder=self.bundled_clips;self.ready=True
                if self.output is not None:self.output.warm([self.folder/(k+'.wav') for k in AUDIO_PHRASES])
                self.events.put(('ready','Free neural driving cues ready.'))
            except (OSError,wave.Error,ValueError) as exc:self.events.put(('error',str(exc)))
            return
        if sys.platform!='win32':
            self.events.put(('error','Braking cue audio requires Windows.'));return
        self.preparing=True
        def worker():
            try:
                self.folder.mkdir(parents=True,exist_ok=True)
                clips=[]
                for key,text in AUDIO_PHRASES.items():
                    path=self.folder/(key+'.wav')
                    valid=False
                    try:
                        with wave.open(str(path),'rb') as cached:
                            valid=.05<cached.getnframes()/cached.getframerate()<3
                    except (OSError,wave.Error,EOFError):pass
                    if not valid:clips.append(dict(path=str(path),text=text))
                if clips:
                    script=Path(__file__).with_name('render_cues.ps1').read_text(encoding='utf-8')
                    encoded=base64.b64encode(script.encode('utf-16-le')).decode('ascii')
                    result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',encoded],
                        input=json.dumps(dict(voice_id=self.voice_id,clips=clips)),text=True,capture_output=True,timeout=45,creationflags=0x08000000)
                    if result.returncode:raise OSError('Could not prepare braking voice clips. Check the selected SAPI voice is installed.')
                for key in AUDIO_PHRASES:
                    with wave.open(str(self.folder/(key+'.wav')),'rb') as f:
                        duration=f.getnframes()/f.getframerate()
                    if not .05<duration<4.5:raise ValueError('Invalid cached braking voice clip.')
                    self.durations[key]=duration
                self.ready=True;self.events.put(('ready','Braking voice clips ready. Enable cues after establishing a clean reference.'))
            except (OSError,ValueError,wave.Error,EOFError,subprocess.TimeoutExpired) as exc:
                self.events.put(('error',str(exc)))
            finally:self.preparing=False
        threading.Thread(target=worker,daemon=True).start()

    def play(self,key):
        if not self.ready:return False
        if self.output is not None:
            if not self.output.play(self.folder/(key+'.wav')):return False
            self.until=time.monotonic()+self.durations[key]+self.output.latency;return True
        if sys.platform!='win32':return False
        import winsound
        try:
            winsound.PlaySound(str(self.folder/(key+'.wav')),winsound.SND_FILENAME|winsound.SND_ASYNC|winsound.SND_NODEFAULT)
            self.until=time.monotonic()+self.durations[key]
            return True
        except RuntimeError:
            self.events.put(('error','Could not play braking cue audio.'));return False

    def stop(self):
        if self.output is not None:self.output.stop()
        if sys.platform=='win32':
            import winsound
            winsound.PlaySound(None,0)
        self.until=0.
