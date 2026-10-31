"""Restore exact publisher assets using the bundled revision and SHA256 manifest."""
from pathlib import Path
import json,hashlib,urllib.request,concurrent.futures
root=Path(__file__).resolve().parent/'neural_assets/supertonic'
manifest=json.loads((root/'SOURCES.json').read_text())
base='https://huggingface.co/'+manifest['repository']+'/resolve/'+manifest['revision']+'/'
def restore(item):
 path=root/item['file']
 if not path.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe asset path')
 if path.is_file() and path.stat().st_size==item['size'] and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']:return item['file']
 path.parent.mkdir(parents=True,exist_ok=True);part=path.with_name(path.name+'.download');digest=hashlib.sha256();size=0
 try:
  with urllib.request.urlopen(base+item['file']+'?download=true',timeout=120) as response,part.open('wb') as output:
   while True:
    block=response.read(1024*1024)
    if not block:break
    size+=len(block)
    if size>item['size']:raise ValueError('Asset exceeds declared size')
    output.write(block);digest.update(block)
  if size!=item['size'] or digest.hexdigest()!=item['sha256']:raise ValueError('Publisher asset checksum mismatch')
  part.replace(path);return item['file']
 finally:part.unlink(missing_ok=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for name in pool.map(restore,manifest['files']):print('Verified',name,flush=True)
