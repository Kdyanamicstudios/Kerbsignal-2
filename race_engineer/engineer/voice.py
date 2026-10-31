"""Local microphone recognition and optional installed Windows voice output."""
import base64
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
from .microphone import MicrophoneCapture
from .local_engineer import WakeController

COMMANDS = {
    'engineer microphone check':'mic_check',
    'engineer explain that':'explain',
    'engineer session recap':'recap',
    'engineer passing opportunities':'opportunities',
    'engineer can you hear me':'mic_check',
    'engineer what track am i on':'track',
    'engineer identify track':'track',
    'engineer where am i on track':'position',
    'engineer what car am i driving':'car',
    'engineer identify my car':'car',
    'engineer last lap':'last_lap',
    'engineer tires':'tires',
    'engineer weather':'weather',
    'engineer abs':'abs',
    'engineer traction control':'tc',
    'engineer where am i losing time':'review',
    'engineer compare line':'line',
    'engineer status':'status',
    'engineer setup':'setup',
    'engineer enable braking cues':'enable_cues',
    'engineer disable braking cues':'disable_cues',
    'engineer play focus music':'focus_music',
    'engineer start focus music':'focus_music',
    'engineer open youtube':'focus_music',
    'engineer mute':'mute',
    'engineer unmute':'unmute',
}


class Speech:
    def __init__(self):
        self.events = queue.Queue()
        self.muted = False
        self.mic = None
        self.capture=None;self.test_mode=False;self.decoder=None;self.mic_state="stopped"
        self.speaking = False
        self.process=None;self.generation=0;self.lock=threading.Lock()
        self.quiet=False;self.cue_until=0.
        self.voice_id=""
        self.neural=None;self.neural_voice="am_michael"
        self.wake=WakeController()

    def interrupt(self):
        if self.neural:self.neural.stop()
        with self.lock:
            self.generation+=1
            process=self.process;self.process=None;self.speaking=False
        if process and process.poll() is None:
            try:process.terminate()
            except OSError:pass

    def say(self, text, force=False):
        if (self.muted and not force) or self.speaking or self.quiet or time.monotonic()<self.cue_until or sys.platform != 'win32':
            return
        self.speaking=True;self.generation+=1;generation=self.generation
        if self.neural:
            voice=self.neural_voice
            def speak_neural():
                try:
                    path=self.neural.render(text,voice)
                    if generation!=self.generation:return
                    self.neural.play(path)
                    end=time.monotonic()+self.neural.duration(path)
                    while generation==self.generation and time.monotonic()<end:time.sleep(.05)
                except Exception:
                    if generation==self.generation:self.events.put(('error','Free neural voice unavailable. Check the complete updated app package.'))
                finally:
                    if generation==self.generation:self.speaking=False
            threading.Thread(target=speak_neural,daemon=True).start();return
        def run():
            process=None
            try:
                code=Path(__file__).with_name("speak.ps1").read_text(encoding="utf-8")
                encoded=base64.b64encode(code.encode("utf-16-le")).decode("ascii")
                with self.lock:
                    if generation!=self.generation:return
                    process=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',encoded],
                        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',creationflags=0x08000000)
                    self.process=process
                process.communicate(input=json.dumps(dict(voice_id=self.voice_id,text=text)),timeout=30)
                if process.returncode and generation==self.generation:
                    self.events.put(('error','Voice output unavailable. Check that your selected SAPI voice is installed.'))
            except (OSError,subprocess.TimeoutExpired):
                if process and process.poll() is None:process.kill();process.communicate()
                self.events.put(('error','Voice output unavailable. Check that your selected SAPI voice is installed.'))
            finally:
                if generation==self.generation:
                    self.speaking=False;self.process=None
        threading.Thread(target=run,daemon=True).start()

    def refresh_voices(self):
        if sys.platform!='win32':
            self.events.put(('error','Installed voice detection requires Windows.'));return
        def run():
            try:
                code=Path(__file__).with_name('list_voices.ps1').read_text(encoding='utf-8')
                encoded=base64.b64encode(code.encode('utf-16-le')).decode('ascii')
                result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',encoded],
                    text=True,encoding='utf-8',capture_output=True,timeout=20,creationflags=0x08000000)
                if result.returncode:raise OSError('Could not list installed SAPI voices.')
                voices=json.loads(result.stdout)
                if not isinstance(voices,list):raise ValueError('Invalid voice list.')
                self.events.put(('voices',voices))
            except (OSError,ValueError,subprocess.TimeoutExpired):
                self.events.put(('error','Could not list installed SAPI voices.'))
        threading.Thread(target=run,daemon=True).start()

    def start_mic(self,device='System default',gain=1,test=False):
        if sys.platform!='win32':
            self.events.put(('error','Microphone recognition requires the Windows app.'));return False
        self.stop_mic();self.test_mode=test
        token=object();self.mic=token;self.mic_state='starting'
        session={'decoder':None,'suppressed':False}
        def failed(message):
            if self.mic is not token:return
            self.mic_state='error';self.events.put(('mic_error','Microphone / recognition: '+str(message)))
        def result(text,confidence):
            if self.mic is token:self.recognized(text,'—' if confidence is None else f'{confidence:.2f}',test)
        def partial(text):
            if self.mic is token:self.events.put(('partial',text))
        def feed(pcm):
            if self.mic is not token:return
            decoder=session['decoder']
            if decoder is None:return
            if not test and (self.speaking or time.monotonic()<self.cue_until):
                if not session['suppressed']:decoder.reset();session['suppressed']=True
                return
            if session['suppressed']:decoder.reset();session['suppressed']=False
            decoder.feed(pcm)
        capture=MicrophoneCapture(device,gain,feed,target_rate=None,on_error=failed)
        self.capture=capture
        def start():
            decoder=None
            try:
                info=capture.start()
                if self.mic is not token:capture.close();return
                self.events.put(('input_ready',f'Input ready: {info["device"]} · {info["sample_rate"]} Hz · {info["channels"]} channel(s). Loading local recognition…'))
                from .offline_recognition import LocalRecognizer
                model=Path(__file__).with_name('speech_assets')/'vosk-model-small-en-us-0.15'
                decoder=LocalRecognizer(model,info['sample_rate'],result,partial)
                if self.mic is not token:decoder.close();capture.close();return
                session['decoder']=decoder;self.decoder=decoder;self.mic_state='listening'
                self.events.put(('ready','Listening locally. '+('Say anything to test recognition; test mode does not execute commands.' if test else 'Say Hey Kerby, then ask your question.')))
            except Exception as exc:
                if decoder:decoder.close()
                capture.close();failed(str(exc))
        threading.Thread(target=start,daemon=True).start();return True

    def recognized(self,phrase,confidence,test=False):
        self.events.put(('heard',phrase+' (confidence '+confidence+')'))
        if test or self.speaking or time.monotonic()<self.cue_until:return
        if phrase.lower() in COMMANDS:self.events.put(('command',COMMANDS[phrase.lower()]));return
        routed=self.wake.route(phrase)
        if routed:self.events.put(routed)

    def stop_mic(self):
        self.wake.reset()
        self.mic=None;capture=self.capture;self.capture=None
        decoder=self.decoder;self.decoder=None;self.mic_state='stopped'
        if capture:
            try:capture.close()
            except Exception:pass
        if decoder:
            try:decoder.close()
            except Exception:pass
