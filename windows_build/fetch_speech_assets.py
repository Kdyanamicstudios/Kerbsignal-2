"""Build-time, verified downloads for the offline recognizer. Never run by app."""
from pathlib import Path
import urllib.request,json,hashlib,zipfile,concurrent.futures
ROOT=Path(__file__).resolve().parent
MODEL_URL='https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip'

def fetch(url,target,expected=None):
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=target.with_suffix(target.suffix+'.download')
    with urllib.request.urlopen(url,timeout=60) as r,temporary.open('wb') as f:
        while chunk:=r.read(1048576):f.write(chunk)
    sha=hashlib.sha256(temporary.read_bytes()).hexdigest()
    if expected and sha!=expected:raise ValueError('Speech download checksum mismatch')
    temporary.replace(target)
    return dict(file=target.name,url=url,size=target.stat().st_size,sha256=sha)

if __name__=='__main__':
    meta=json.load(urllib.request.urlopen('https://pypi.org/pypi/vosk/0.3.45/json',timeout=30))
    files=[x for x in meta['urls'] if x['filename'].endswith(('py3-none-win_amd64.whl','py3-none-manylinux_2_12_x86_64.manylinux2010_x86_64.whl'))]
    jobs=[(x['url'],ROOT/('speech_wheels' if 'win_amd64' in x['filename'] else 'linux_speech_wheels')/x['filename'],x['digests']['sha256']) for x in files]
    jobs.append((MODEL_URL,ROOT/'downloads/vosk-model-small-en-us-0.15.zip',None))
    with concurrent.futures.ThreadPoolExecutor(3) as pool:records=list(pool.map(lambda job:fetch(*job),jobs))
    modelzip=ROOT/'downloads/vosk-model-small-en-us-0.15.zip';out=ROOT/'speech_assets';out.mkdir(exist_ok=True)
    with zipfile.ZipFile(modelzip) as z:
        for name in z.namelist():
            if not (out/name).resolve().is_relative_to(out.resolve()):raise ValueError('Unsafe speech-model archive')
        z.extractall(out)
    manifest=dict(engine='Vosk',version='0.3.45',model='vosk-model-small-en-us-0.15',license='Apache-2.0',downloads=records,
        files=[dict(file=str(p.relative_to(out)),size=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in out.rglob('*') if p.is_file() and p.name!='SOURCES.json'])
    (out/'SOURCES.json').write_text(json.dumps(manifest,indent=2))
    print('Offline recognizer and model fetched, pinned and verified.',flush=True)
