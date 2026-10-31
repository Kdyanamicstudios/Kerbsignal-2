"""Actual PCM conversion, selected-device negotiation and failure propagation."""
import array,math,threading,time,unittest
from types import SimpleNamespace
from unittest.mock import patch
from engineer.microphone import MicrophoneCapture

class Stream:
    def __init__(self,**kw):self.options=kw;self.active=False
    def start(self):self.active=True
    def abort(self):self.active=False
    def close(self):self.active=False

class CaptureTests(unittest.TestCase):
    def sd(self):
        rows=[dict(name='Other',hostapi=0,max_input_channels=1,default_samplerate=48000),dict(name='Headset',hostapi=1,max_input_channels=2,default_samplerate=48000)]
        def query(device=None,kind=None):return rows if kind is None else rows[1 if device is None else device]
        return SimpleNamespace(query_devices=query,query_hostapis=lambda i:dict(name=['MME','WASAPI'][i]),check_input_settings=lambda **kw:None,RawInputStream=Stream)
    def test_saved_device_survives_reordered_numeric_index(self):
        sd=self.sd();self.assertEqual(MicrophoneCapture.resolve_device(sd,'0: Headset'),1)
        self.assertEqual(MicrophoneCapture.resolve_device(sd,'Headset [WASAPI]'),1)
        with self.assertRaises(ValueError):MicrophoneCapture.resolve_device(sd,'Missing [WASAPI]')
    def test_native_rate_stereo_fallback_and_pcm_reaches_meter_and_consumer(self):
        sd=self.sd();streams=[];delivered=[];done=threading.Event()
        def create(**kw):
            if kw['channels']==1:raise OSError('Stereo input required')
            result=Stream(**kw);streams.append(result);return result
        sd.RawInputStream=create
        def audio(pcm):delivered.append(pcm);done.set()
        c=MicrophoneCapture('Headset [WASAPI]',on_audio=audio,target_rate=None)
        with patch.dict('sys.modules',{'sounddevice':sd}):
            info=c.start()
            self.assertEqual(info['sample_rate'],48000);self.assertEqual(info['channels'],2)
            samples=array.array('h',[0,6000]*1440)
            streams[-1].options['callback'](samples.tobytes(),1440,None,None)
            self.assertTrue(done.wait(1));self.assertGreater(c.level_db,-20)
            self.assertEqual(array.array('h',delivered[0])[0],6000)
            self.assertTrue(c.running);c.close();self.assertFalse(c.running)
    def test_opposite_stereo_channels_do_not_cancel_microphone(self):
        c=MicrophoneCapture(target_rate=None);c.sample_rate=48000;c.channels=2
        out=array.array('h',c.convert(array.array('h',[5000,-5000]*300).tobytes()))
        self.assertTrue(all(v==5000 for v in out));self.assertGreater(c.level_db,-20)
    def test_gain_is_clipped_and_clipping_is_visible(self):
        c=MicrophoneCapture(gain=3,target_rate=None);c.sample_rate=48000
        out=array.array('h',c.convert(array.array('h',[20000,-20000]).tobytes()))
        self.assertEqual(list(out),[32767,-32768]);self.assertTrue(c.clipping)
    def test_streaming_resampler_has_consistent_boundary_timing(self):
        raw=array.array('h',[int(10000*math.sin(i*.03)) for i in range(4410)]).tobytes()
        whole=MicrophoneCapture();whole.sample_rate=44100
        a=array.array('h',whole.convert(raw))
        chunks=MicrophoneCapture();chunks.sample_rate=44100
        b=array.array('h')
        for offset in range(0,len(raw),882):b.frombytes(chunks.convert(raw[offset:offset+882]))
        self.assertEqual(len(a),len(b));self.assertLessEqual(max(abs(x-y) for x,y in zip(a,b)),1)
    def test_recognizer_failure_is_reported_and_closes_input(self):
        sd=self.sd();errors=[];failed=threading.Event()
        def broken(pcm):raise OSError('Decoder failed')
        def on_error(text):errors.append(text);failed.set()
        c=MicrophoneCapture(on_audio=broken,target_rate=None,on_error=on_error)
        with patch.dict('sys.modules',{'sounddevice':sd}):
            c.start();stream=c.stream;stream.options['callback'](array.array('h',[4000]*300).tobytes(),300,None,None)
            self.assertTrue(failed.wait(1));c.close()
            self.assertIn('Decoder failed',errors);self.assertFalse(c.running)
