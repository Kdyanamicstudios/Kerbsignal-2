"""Bundled Pocket TTS CPU runtime. Only shipped, licensed voice embeddings load.

All paths are local. This wrapper does not download models, clone user voices,
start an HTTP server, or require an API account.
"""
from pathlib import Path
import hashlib,json,os,subprocess,sys,threading,wave,array

VOICE_FILES={'pt_bill':'bill_boerst','pt_peter':'peter_yearsley','pt_michael':'michael'}

class PocketVoice:
    def __init__(self,assets):
        self.assets=Path(assets).resolve();self.process=None;self.lock=threading.Lock();self.verified=False
    def load(self):
        if self.verified:return
        manifest=json.loads((self.assets/'SOURCES.json').read_text())
        for item in manifest['files']:
            p=self.assets/item['file']
            if not p.resolve().is_relative_to(self.assets):raise ValueError('Invalid voice-asset path')
            if p.stat().st_size!=item['size'] or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:
                raise ValueError('Incomplete Pocket voice assets')
        config=(self.assets/'config.yaml').read_text()
        if 'hf://' in config or 'https://' in config or 'http://' in config:raise ValueError('Voice config must be offline')
        self.verified=True
    def binary(self):
        if sys.platform=='win32':return self.assets/'pocket-tts.exe'
        override=os.environ.get('KERBSIGNAL_POCKET_BINARY')
        if not override:raise OSError('The bundled application voice runtime requires Windows')
        return Path(override).resolve()
    def write(self,text,voice,path):
        if voice not in VOICE_FILES:raise ValueError('Unknown Pocket voice')
        self.load();path=Path(path).resolve()
        command=[str(self.binary()),'generate','--config','config.yaml','--voice',
                 'voices/'+VOICE_FILES[voice]+'.safetensors','--text',text,
                 '--output-path',str(path),'--temperature','0.3','--quiet']
        env=os.environ.copy()
        for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','RAYON_NUM_THREADS'):env[key]='2'
        env['HF_HUB_OFFLINE']='1';env['HF_HUB_DISABLE_TELEMETRY']='1'
        options=dict(cwd=str(self.assets),env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        if sys.platform=='win32':options['creationflags']=0x08000000
        process=subprocess.Popen(command,**options)
        with self.lock:self.process=process
        try:
            _,error=process.communicate(timeout=45)
            if process.returncode:raise OSError('Pocket voice generation was interrupted or failed')
            with wave.open(str(path),'rb') as f:
                if f.getnchannels()!=1 or f.getsampwidth()!=2 or f.getframerate()!=24000:raise ValueError('Unexpected voice audio format')
                audio=array.array('h',f.readframes(f.getnframes()))
            if not audio or max(map(abs,audio))<60:raise ValueError('Voice output was silent')
        except BaseException:
            if process.poll() is None:process.kill();process.communicate()
            path.unlink(missing_ok=True);raise
        finally:
            with self.lock:
                if self.process is process:self.process=None
    def stop(self):
        with self.lock:process=self.process
        if process is not None and process.poll() is None:
            try:process.terminate()
            except OSError:pass
