"""One local output stream for cached instructions and conversational speech."""
import queue,sys,threading,time,wave
from collections import deque
from pathlib import Path

class AudioOutput:
 def __init__(self):
  self.closed=False;self.stream=None;self.lock=threading.Lock();self.buffer=b'';self.offset=0;self.rate=24000;self.channels=1;self.onsets=deque(maxlen=100);self.clip_id=None
  self.volume=.8;self.device_name='System default';self.events=queue.Queue();self.loading=False
  self.cache={};self.clip_paths=[]
  self.latency=.03;self.last_onset=None;self.requested=None;self.label='Not prepared';self.generation=0
 def configure(self,volume,device_name='System default'):
  self.volume=max(0,min(1,float(volume)));changed=device_name!=self.device_name;self.device_name=device_name
  if changed or self.stream is not None and not getattr(self.stream,'active',True):self.close()
  self.prepare()
 def prepare(self):
  if self.closed or self.stream or self.loading or sys.platform!='win32':return
  self.loading=True;generation=self.generation
  def worker():
   stream=None
   try:
    import sounddevice as sd
    import numpy as np
    device=None
    if self.device_name!='System default':
     device=next((i for i,d in enumerate(sd.query_devices()) if d['max_output_channels']>0 and self.output_label(sd,i,d)==self.device_name),None)
     if device is None:raise OSError('Selected audio device is disconnected. Choose System default or rescan devices.')
    info=sd.query_devices(device,'output');self.rate=int(round(info['default_samplerate']));self.channels=min(2,int(info['max_output_channels']));self.cache.clear()
    stream=sd.RawOutputStream(samplerate=self.rate,channels=self.channels,dtype='int16',device=device,blocksize=0,latency='low',callback=self.callback)
    stream.start()
    with self.lock:
     accepted=generation==self.generation
     if accepted:self.stream=stream;self.latency=float(stream.latency);self.label=self.device_name
    if not accepted:stream.close();return
    self.warm(self.clip_paths)
    self.events.put(('ready',f'Audio ready • {self.latency*1000:.0f} ms reported output latency'))
   except Exception as exc:
    if stream:
     try:stream.close()
     except Exception:pass
    self.label='Unavailable';self.events.put(('error','Audio output unavailable: '+str(exc)))
   finally:
    self.loading=False
    if generation!=self.generation:self.prepare()
  threading.Thread(target=worker,daemon=True).start()
 @staticmethod
 def output_label(sd,i,d):return d['name']+' ['+str(sd.query_hostapis(d['hostapi'])['name'])+']'
 @classmethod
 def devices(cls):
  if sys.platform!='win32':return ['System default']
  import sounddevice as sd
  return ['System default']+list(dict.fromkeys(cls.output_label(sd,i,d) for i,d in enumerate(sd.query_devices()) if d['max_output_channels']>0))
 def callback(self,outdata,frames,timing,status):
  raw=memoryview(outdata).cast('B');raw[:]=b'\x00'*len(raw)
  with self.lock:
   take=min(len(raw),len(self.buffer)-self.offset)
   if take>0:
    if self.offset==0:
     self.last_onset=time.monotonic()+max(0,timing.outputBufferDacTime-timing.currentTime)
     self.onsets.append(dict(clip=self.clip_id,requested=self.requested,estimated_audible=self.last_onset,delay_ms=round((self.last_onset-self.requested)*1000,1)))
    raw[:take]=self.buffer[self.offset:self.offset+take];self.offset+=take
 def warm(self,paths):
  self.clip_paths=list(paths)
  if not self.stream:return
  def worker():
   for path in self.clip_paths:
    try:self.clip(path)
    except (OSError,ValueError,wave.Error):pass
  threading.Thread(target=worker,daemon=True).start()
 def clip(self,path):
  key=(str(path),self.rate,self.channels,self.volume)
  if key in self.cache:return self.cache[key]
  import numpy as np
  with wave.open(str(path),'rb') as f:
   if f.getnchannels()!=1 or f.getsampwidth()!=2:raise ValueError('Unsupported voice clip format')
   rate=f.getframerate();values=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2')
  if rate!=self.rate:
   count=round(len(values)*self.rate/rate)
   values=np.interp(np.arange(count)*rate/self.rate,np.arange(len(values)),values)
  if self.channels>1:values=np.repeat(values,self.channels)
  raw=np.clip(values*self.volume,-32768,32767).astype('<i2').tobytes()
  # Keep only short instruction clips in memory; conversational renders stay on disk.
  if len(raw)<=self.rate*2*self.channels*5:self.cache[key]=raw
  return raw
 def play(self,path):
  if not self.stream or not getattr(self.stream,'active',True):return False
  raw=self.clip(path)
  with self.lock:self.buffer=raw;self.offset=0;self.requested=time.monotonic();self.last_onset=None;self.clip_id=Path(path).stem
  return True
 def stop(self):
  with self.lock:self.buffer=b'';self.offset=0
 def close(self,permanent=False):
  if permanent:self.closed=True
  with self.lock:
   self.generation+=1;stream=self.stream;self.stream=None;self.buffer=b'';self.offset=0
  if stream:
   try:stream.close()
   except Exception:pass
