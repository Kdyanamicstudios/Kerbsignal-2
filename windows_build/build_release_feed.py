"""Package a Windows installer as <=20 MiB verified release-feed assets."""
from pathlib import Path
import argparse,hashlib,json,sys
p=argparse.ArgumentParser();p.add_argument('installer');p.add_argument('version');p.add_argument('origin');p.add_argument('destination');a=p.parse_args()
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'race_engineer'))
from engineer.updater import validate_manifest,version
version(a.version);source=Path(a.installer);root=Path(a.destination);release=root/'releases'/a.version;release.mkdir(parents=True,exist_ok=True)
chunks=[];total=0;whole=hashlib.sha256()
with source.open('rb') as f:
 while True:
  block=f.read(20*1024*1024)
  if not block:break
  if not chunks and block[:2]!=b'MZ':raise ValueError('Not a Windows installer')
  digest=hashlib.sha256(block).hexdigest();name=f'{len(chunks):03d}-{digest}.bin';(release/name).write_bytes(block)
  chunks.append(dict(url=a.origin.rstrip('/')+'/releases/'+a.version+'/'+name,size=len(block),sha256=digest));total+=len(block);whole.update(block)
manifest=dict(format='kerbsignal-release-v1',product='RaceEngineer',display_name='KerbSignal',platform='windows-x64',version=a.version,size=total,sha256=whole.hexdigest(),chunks=chunks)
validate_manifest(manifest,a.origin.rstrip('/')+'/stable.json');(root/'stable.json').write_text(json.dumps(manifest,indent=2)+'\n')
(root/'health.json').write_text(json.dumps(dict(product='KerbSignal',version=a.version,chunk_count=len(chunks),installer_bytes=total)))
print(json.dumps(dict(version=a.version,chunks=len(chunks),size=total,sha256=whole.hexdigest())))
