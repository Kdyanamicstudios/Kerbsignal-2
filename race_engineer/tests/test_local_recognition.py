import json,queue,tempfile,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from engineer.offline_recognition import LocalRecognizer
from engineer.voice import Speech

class RecognizerTests(unittest.TestCase):
    def test_native_sample_rate_and_local_model_are_used_and_partials_are_not_repeated(self):
        calls=[]
        class Decoder:
            def __init__(self,model,rate):calls.append(('rate',rate));self.n=0
            def SetWords(self,flag):self.words=flag
            def AcceptWaveform(self,pcm):self.n+=1;return self.n==3
            def PartialResult(self):return json.dumps(dict(partial='engineer microphone'))
            def Result(self):return json.dumps(dict(text='engineer microphone check',result=[dict(conf=.9),dict(conf=1)]))
            def Reset(self):calls.append(('reset',))
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);(p/'am').mkdir();(p/'am/final.mdl').write_bytes(b'test fixture')
            def model(path):calls.append(('model',path));return 'loaded'
            with patch.dict('sys.modules',{'vosk':SimpleNamespace(Model=model,KaldiRecognizer=Decoder,SetLogLevel=lambda n:None)}):
                results=[];partials=[];r=LocalRecognizer(p,48000,lambda text,conf:results.append((text,conf)),partials.append)
                for _ in range(3):r.feed(b'\0\0'*100)
                self.assertEqual(partials,['engineer microphone']);self.assertEqual(results,[('engineer microphone check',.95)])
                self.assertIn(('rate',48000.),calls);self.assertEqual(calls[0],('model',str(p.resolve())))
                r.close();r.feed(b'x');self.assertEqual(len(results),1)
    def test_missing_bundled_model_reports_a_clear_error(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(OSError,'recognition model is missing'):LocalRecognizer(folder,16000,None)

class FakeCapture:
    def __init__(self,device,gain,on_audio,**kw):self.device=device;self.on_audio=on_audio;self.kw=kw;self.closed=False
    def start(self):return dict(device=self.device,sample_rate=48000,channels=2)
    def close(self):self.closed=True
class FakeDecoder:
    def __init__(self,path,rate,on_result,on_partial):self.rate=rate;self.result=on_result;self.partial=on_partial;self.closed=False
    def feed(self,pcm):self.partial('engineer microphone');self.result('engineer microphone check',.98)
    def reset(self):pass
    def close(self):self.closed=True

class SpeechBridgeTests(unittest.TestCase):
    def start(self,test=False,capture=FakeCapture):
        self.enterContext(patch('engineer.voice.sys',SimpleNamespace(platform='win32')))
        self.enterContext(patch('engineer.voice.MicrophoneCapture',capture))
        self.enterContext(patch('engineer.offline_recognition.LocalRecognizer',FakeDecoder))
        s=Speech();self.assertTrue(s.start_mic('Selected headset',1.5,test))
        events=[]
        while True:
            e=s.events.get(timeout=2);events.append(e)
            if e[0] in ('ready','mic_error'):break
        return s,events
    def test_selected_input_and_recognizer_share_native_rate(self):
        s,events=self.start();self.assertEqual(s.capture.device,'Selected headset')
        self.assertIsNone(s.capture.kw['target_rate']);self.assertEqual(s.decoder.rate,48000)
        self.assertEqual(s.mic_state,'listening');self.assertEqual([e[0] for e in events],['input_ready','ready'])
        capture=s.capture;decoder=s.decoder;capture.on_audio(b'\x01\0'*100)
        events=[]
        while not s.events.empty():events.append(s.events.get())
        self.assertIn(('command','mic_check'),events);self.assertTrue(any(e[0]=='partial' for e in events))
        s.stop_mic();self.assertTrue(capture.closed);self.assertTrue(decoder.closed)
    def test_recognition_test_shows_text_without_executing_commands(self):
        s,events=self.start(test=True);s.capture.on_audio(b'\x01\0'*100)
        events=[]
        while not s.events.empty():events.append(s.events.get())
        self.assertTrue(any(e[0]=='heard' for e in events));self.assertFalse(any(e[0]=='command' for e in events));s.stop_mic()
    def test_failed_start_does_not_claim_recognition_is_ready(self):
        class Broken(FakeCapture):
            def start(self):raise OSError('Microphone permission denied')
        s,events=self.start(capture=Broken)
        self.assertEqual(s.mic_state,'error');self.assertFalse(any(e[0]=='ready' for e in events))
        self.assertIn('permission denied',events[-1][1]);s.stop_mic()
    def test_engineer_echo_is_not_executed_as_a_driver_command(self):
        s,events=self.start();s.speaking=True;s.capture.on_audio(b'\x01\0'*100)
        self.assertTrue(s.events.empty());s.stop_mic()
