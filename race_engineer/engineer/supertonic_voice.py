"""Free local Supertonic 3 preset voices, CPU only; no account or uploads."""
import os
from pathlib import Path
class SupertonicVoice:
 def __init__(self,folder):
  self.folder=Path(folder);self.model=None;self.styles={}
 def load(self):
  if self.model:return
  os.environ['ORT_DISABLE_TELEMETRY']='1'
  import onnxruntime as ort
  ort.disable_telemetry_events()
  from .third_party import supertonic as sdk
  opts=ort.SessionOptions();opts.intra_op_num_threads=2;opts.inter_op_num_threads=1;opts.log_severity_level=3
  onnx=self.folder/'onnx'
  sessions=sdk.load_onnx_all(str(onnx),opts,['CPUExecutionProvider'])
  self.model=sdk.TextToSpeech(sdk.load_cfgs(str(onnx)),sdk.load_text_processor(str(onnx)),*sessions)
 def create(self,text,voice,speed=1.0):
  if voice not in ('M1','M2','M3','M4','M5'):raise ValueError('Unknown natural voice preset')
  self.load()
  if voice not in self.styles:
   from .third_party.supertonic import load_voice_style
   self.styles[voice]=load_voice_style([str(self.folder/'voice_styles'/(voice+'.json'))])
  import numpy as np
  for attempt in range(3):
   wav,duration=self.model(str(text),'en',self.styles[voice],total_step=8,speed=speed,silence_duration=.18)
   size=min(wav.shape[-1],max(1,int(float(duration[0])*self.model.sample_rate)))
   result=wav[0,:size]
   if np.all(np.isfinite(result)) and float(np.max(np.abs(result)))>.004 and float(np.sqrt(np.mean(result*result)))>.0003:
    return result,self.model.sample_rate
  raise ValueError('Natural voice produced an empty or silent utterance. Try the preview again or select another preset.')
