"""One selected-device capture stream for the input meter and recognizer.

The PortAudio callback only copies audio. Conversion, metering and recognition
run off the audio callback. Nothing is recorded to disk or uploaded.
"""
import math,queue,threading,time

class MicrophoneCapture:
    def __init__(self,device='System default',gain=1,on_audio=None,target_rate=16000,on_error=None):
        self.target_rate=target_rate;self.device=device;self.gain=max(.1,min(3,float(gain)))
        self.on_audio=on_audio;self.on_error=on_error;self.level_db=-80.;self.clipping=False
        self.stream=None;self.queue=queue.Queue(3);self.stopping=threading.Event();self.error=''
        self.sample_rate=None;self.channels=1;self.label='Not started';self.worker=None
        self.dropped_blocks=0;self.last_audio=None;self._seen=0;self._next=0.;self._last=None
    @staticmethod
    def input_label(sd,i,d):
        try:api=sd.query_hostapis(d['hostapi'])['name']
        except (KeyError,TypeError,AttributeError):api='Input'
        return d['name']+' ['+str(api)+']'
    @classmethod
    def devices(cls):
        import sounddevice as sd
        return ['System default']+list(dict.fromkeys(cls.input_label(sd,i,d) for i,d in enumerate(sd.query_devices()) if d['max_input_channels']>0))
    @classmethod
    def resolve_device(cls,sd,label):
        if label=='System default':return None
        rows=sd.query_devices()
        # Retain saved 0.14 choices even if device enumeration order changed.
        legacy_name=None
        try:
            index,name=label.split(':',1);index=int(index);legacy_name=name.strip()
            if 0<=index<len(rows) and rows[index]['max_input_channels']>0 and rows[index]['name']==legacy_name:return index
        except (ValueError,AttributeError):pass
        for i,d in enumerate(rows):
            if d['max_input_channels']>0 and (cls.input_label(sd,i,d)==label or legacy_name and d['name']==legacy_name):return i
        raise ValueError('Selected microphone is unavailable. Rescan devices and choose an input.')
    def start(self):
        import sounddevice as sd
        # Initialize conversion before opening the stream. The first NumPy
        # import can otherwise stall the consumer and discard the first words.
        import numpy
        selected=self.resolve_device(sd,self.device);info=sd.query_devices(selected,'input')
        maximum=int(info.get('max_input_channels',0))
        if maximum<1:raise ValueError('The selected device has no microphone input channels.')
        native=int(round(float(info.get('default_samplerate') or 48000)))
        rates=list(dict.fromkeys((native,48000,44100,16000)))
        channel_options=list(dict.fromkeys((1,min(2,maximum))))
        failures=[]
        self.stopping.clear();self.error='';self.level_db=-80.;self.clipping=False
        self._seen=0;self._next=0.;self._last=None
        for rate in rates:
            for channels in channel_options:
                stream=None
                token=object();self._stream_token=token
                try:
                    checker=getattr(sd,'check_input_settings',None)
                    if checker:checker(device=selected,samplerate=rate,channels=channels,dtype='int16')
                    def callback(raw,frames,timing,status,token=token):
                        if self.stopping.is_set() or self._stream_token is not token:return
                        item=(bytes(raw),time.monotonic())
                        try:self.queue.put_nowait(item)
                        except queue.Full:
                            try:self.queue.get_nowait()
                            except queue.Empty:pass
                            self.dropped_blocks+=1
                            try:self.queue.put_nowait(item)
                            except queue.Full:pass
                    def finished(token=token):
                        if self._stream_token is token and self.stream is not None and not self.stopping.is_set():
                            self.error='Microphone input stopped unexpectedly. Check the selected device.'
                            self.stopping.set()
                            if self.on_error:self.on_error(self.error)
                    stream=sd.RawInputStream(device=selected,samplerate=rate,channels=channels,dtype='int16',blocksize=max(1,round(rate*.03)),callback=callback,finished_callback=finished)
                    self.sample_rate=rate;self.channels=channels
                    stream.start();self.stream=stream
                    self.label=self.input_label(sd,selected,info)
                    self.worker=threading.Thread(target=self._send,daemon=True);self.worker.start()
                    return dict(device=self.label,sample_rate=rate,channels=channels,recognition_rate=self.target_rate or rate)
                except Exception as exc:
                    failures.append(str(exc))
                    if stream:
                        try:stream.close()
                        except Exception:pass
                    while not self.queue.empty():
                        try:self.queue.get_nowait()
                        except queue.Empty:break
        self.stopping.set()
        raise OSError('Cannot open the selected microphone. Check Windows microphone access and the input device. '+(failures[-1] if failures else 'No supported input format.'))
    def _resample(self,values):
        if not self.target_rate or self.target_rate==self.sample_rate:return values
        import numpy as np
        origin=self._seen if self._last is None else self._seen-1
        joined=values if self._last is None else np.concatenate(([self._last],values))
        end=origin+len(joined)-1;step=self.sample_rate/self.target_rate
        count=max(0,math.floor((end-self._next)/step)+1)
        positions=self._next+np.arange(count)*step-origin
        result=np.interp(positions,np.arange(len(joined)),joined)
        self._next+=count*step;self._seen+=len(values);self._last=values[-1]
        return result
    def convert(self,raw):
        import numpy as np
        values=np.frombuffer(raw,dtype='<i2').astype(np.float32)
        if not len(values):return b''
        if len(values)%self.channels:raise ValueError('Microphone returned an incomplete audio frame.')
        if self.channels>1:
            values=values.reshape(-1,self.channels)
            # Pick the active channel; averaging phase-inverted stereo can
            # cancel a perfectly valid microphone signal.
            strongest=int(np.argmax(np.mean(values*values,axis=0)));values=values[:,strongest]
        values=values*self.gain
        rms=float(np.sqrt(np.mean(values*values)))/32768
        self.level_db=min(0.,max(-80.,20*math.log10(max(rms,1e-4))))
        self.clipping=bool(np.any(np.abs(values)>=32767));self.last_audio=time.monotonic()
        values=self._resample(values)
        return np.clip(values,-32768,32767).astype('<i2').tobytes()
    def _send(self):
        try:
            while not self.stopping.is_set():
                try:raw,when=self.queue.get(timeout=.1)
                except queue.Empty:continue
                if time.monotonic()-when>.5:self.dropped_blocks+=1;continue
                pcm=self.convert(raw)
                if pcm and self.on_audio:self.on_audio(pcm)
        except Exception as exc:
            self.error=str(exc)
            if self.on_error:self.on_error(self.error)
            self.close()
    @property
    def running(self):return self.stream is not None and bool(getattr(self.stream,'active',False)) and not self.stopping.is_set()
    def close(self):
        self.stopping.set();stream=self.stream;self.stream=None
        if stream:
            try:stream.abort()
            except Exception:pass
            try:stream.close()
            except Exception:pass
        if self.worker and self.worker is not threading.current_thread():self.worker.join(timeout=.3)
        self.level_db=-80.;self.clipping=False
    stop=close
