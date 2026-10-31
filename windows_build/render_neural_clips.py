from pathlib import Path
import os,sys,wave,time,array
os.environ['ORT_DISABLE_TELEMETRY']='1'
sys.path.insert(0,str(Path('race_engineer').resolve()))
from engineer.neural_voice import NeuralVoice,VOICES
from engineer.cue_audio import AUDIO_PHRASES as PHRASES
assets=Path('windows_build/neural_assets').resolve()
voice=NeuralVoice(assets,assets/'render_cache')
for code,lang in VOICES.values():
 if not code.startswith('pt_'):continue
 out=assets/'clips'/code;out.mkdir(parents=True,exist_ok=True)
 for key,text in PHRASES.items():
  p=voice.render(text+'.',code,speed=1.05 if code.startswith('st3_') else 1.3)
  # Remove model padding so the configured lead targets audible speech onset.
  with wave.open(str(p),'rb') as f:
   rate=f.getframerate();audio=array.array('h',f.readframes(f.getnframes()))
  threshold=max(60,max(map(abs,audio))*.008)
  audible=[i for i,v in enumerate(audio) if abs(v)>threshold]
  assert audible,(code,key,'silent clip')
  start=max(0,audible[0]-int(rate*.025));end=min(len(audio),audible[-1]+int(rate*.06))
  path=out/(key+'.wav')
  with wave.open(str(path),'wb') as f:
   f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(audio[start:end].tobytes())
  duration=voice.duration(path)
  assert .05<duration<4.5,(code,key,duration)
  print(code,key,round(duration,3),flush=True)
print('Pre-rendered all instruction clips',flush=True)
