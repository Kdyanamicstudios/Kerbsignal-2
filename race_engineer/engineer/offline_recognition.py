"""Bundled English speech recognition. Local model path only, never downloads."""
from pathlib import Path
import json,threading,statistics

class LocalRecognizer:
    _models={};_lock=threading.Lock()
    def __init__(self,model_path,sample_rate,on_result,on_partial=None):
        path=Path(model_path).resolve()
        if not (path/'am/final.mdl').is_file():raise OSError('The offline recognition model is missing. Install the complete updated app.')
        from vosk import Model,KaldiRecognizer,SetLogLevel
        SetLogLevel(-1)
        with self._lock:
            if str(path) not in self._models:self._models[str(path)]=Model(str(path))
            model=self._models[str(path)]
        self.recognizer=KaldiRecognizer(model,float(sample_rate));self.recognizer.SetWords(True)
        self.on_result=on_result;self.on_partial=on_partial;self.previous_partial='';self.closed=False
    def feed(self,pcm):
        if self.closed:return
        if self.recognizer.AcceptWaveform(pcm):
            obj=json.loads(self.recognizer.Result());text=str(obj.get('text','')).strip();self.previous_partial=''
            if text:
                confidence=statistics.mean(w['conf'] for w in obj.get('result',[]) if 'conf' in w) if obj.get('result') else None
                self.on_result(text,confidence)
        elif self.on_partial:
            value=str(json.loads(self.recognizer.PartialResult()).get('partial','')).strip()
            if value!=self.previous_partial:
                self.previous_partial=value;self.on_partial(value)
    def reset(self):
        if not self.closed:self.recognizer.Reset();self.previous_partial=''
    def close(self):self.closed=True
