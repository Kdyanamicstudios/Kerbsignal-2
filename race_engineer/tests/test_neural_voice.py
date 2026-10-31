import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from engineer.neural_voice import NeuralVoice


class NeuralPrivacyTests(unittest.TestCase):
    def test_telemetry_disabled_before_session_creation(self):
        calls=[]
        def session(*args,**kwargs):
            self.assertEqual(os.environ['ORT_DISABLE_TELEMETRY'],'1')
            self.assertEqual(calls,['disable'])
            self.assertEqual(kwargs['providers'],['CPUExecutionProvider'])
            calls.append('session');return 'model-session'
        ort=SimpleNamespace(disable_telemetry_events=lambda:calls.append('disable'),
                            SessionOptions=SimpleNamespace,InferenceSession=session)
        kokoro=SimpleNamespace(Kokoro=SimpleNamespace(from_session=lambda *args:args))
        with tempfile.TemporaryDirectory() as folder,patch.dict('sys.modules',{'onnxruntime':ort,'kokoro_onnx':kokoro}),patch.dict(os.environ,{'ORT_DISABLE_TELEMETRY':'0'}):
            voice=NeuralVoice(folder,Path(folder)/'cache');voice._ensure_model()
            self.assertTrue(voice.model);self.assertEqual(calls,['disable','session'])

    def test_unknown_voice_is_rejected_before_loading(self):
        with tempfile.TemporaryDirectory() as folder:
            voice=NeuralVoice(folder,folder)
            with self.assertRaises(ValueError):voice.render('Test','unknown')
            self.assertIsNone(voice.model)

class NewNaturalVoiceTests(unittest.TestCase):
 def test_free_presets_and_old_accents_remain_available(self):
  from engineer.neural_voice import VOICES,DEFAULT_VOICE
  ids={v[0] for v in VOICES.values()};self.assertTrue({'pt_bill','pt_peter','pt_michael','am_michael','bm_george'}<=ids);self.assertFalse(any(v.startswith('st3_') for v in ids));self.assertEqual(DEFAULT_VOICE,'pt_bill')
 def test_supertonic_cpu_privacy_is_applied_before_sessions(self):
  from engineer.supertonic_voice import SupertonicVoice
  import sys
  calls=[]
  ort=SimpleNamespace(disable_telemetry_events=lambda:calls.append('disable'),SessionOptions=SimpleNamespace)
  def load(*args):
   self.assertEqual(os.environ['ORT_DISABLE_TELEMETRY'],'1');self.assertEqual(calls,['disable']);self.assertEqual(args[2],['CPUExecutionProvider']);self.assertEqual(args[1].intra_op_num_threads,2);calls.append('sessions');return [None]*4
  sdk=SimpleNamespace(load_onnx_all=load,load_cfgs=lambda p:{},load_text_processor=lambda p:None,TextToSpeech=lambda *args:'model')
  with patch.dict(sys.modules,{'onnxruntime':ort,'engineer.third_party.supertonic':sdk}),patch.dict(os.environ,{'ORT_DISABLE_TELEMETRY':'0'}):
   voice=SupertonicVoice('unused');voice.load();self.assertEqual(voice.model,'model');self.assertEqual(calls,['disable','sessions'])
