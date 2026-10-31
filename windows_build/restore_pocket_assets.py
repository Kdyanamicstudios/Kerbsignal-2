"""Developer restore of the pinned offline speech assets; never run by the app."""
from pathlib import Path
import hashlib,json,urllib.request,zipfile,io
root=Path(__file__).resolve().parent/'neural_assets/pocket'
manifest=json.loads((root/'SOURCES.json').read_text())
for item in manifest['sources']:
    target=root/item['file']
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==item['sha256']:continue
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=target.with_suffix(target.suffix+'.download')
    with urllib.request.urlopen(item['url'],timeout=60) as response,temporary.open('wb') as out:
        while chunk:=response.read(1048576):out.write(chunk)
    assert temporary.stat().st_size==item['size'] and hashlib.sha256(temporary.read_bytes()).hexdigest()==item['sha256']
    temporary.replace(target)
archive=manifest['binary_archive']
path=root/'pocket-tts.exe'
expected=next(i['sha256'] for i in manifest['files'] if i['file']=='pocket-tts.exe')
if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
    data=urllib.request.urlopen(archive['url'],timeout=60).read();assert hashlib.sha256(data).hexdigest()==archive['sha256']
    with zipfile.ZipFile(io.BytesIO(data)) as z:path.write_bytes(z.read(archive['member']))
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
print('Pinned Pocket voice assets restored.')
