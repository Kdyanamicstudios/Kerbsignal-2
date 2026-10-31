"""Verify staged or installer-extracted code and speech assets against source."""
from pathlib import Path
import sys,json,hashlib,wave,array,zipfile
root=Path(__file__).resolve().parents[1]
payload=Path(sys.argv[1]) if len(sys.argv)>1 else root/'windows_build/payload'
source=root/'race_engineer'
sys.path.insert(0,str(source))
expected=[source/'app.py']+list((source/'engineer').rglob('*.py'))+list((source/'engineer/assets').glob('*.png'))
for p in expected:
    assert (payload/p.relative_to(source)).read_bytes()==p.read_bytes(),str(p)
info=json.loads((payload/'BUILD_INFO.json').read_text());assert info['version']==__import__('engineer.updater',fromlist=['VERSION']).VERSION
assert set(info['voices'])=={'pt_bill','pt_peter','pt_michael','am_michael','bm_george'}
assets=payload/'engineer/neural_assets';pack=assets/'pocket'
manifest=json.loads((pack/'SOURCES.json').read_text())
for item in manifest['files']:
    p=pack/item['file'];assert p.stat().st_size==item['size'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],item['file']
assert not (assets/'supertonic').exists()
assert (payload/'Third_Party/PocketTTS/MODEL_LICENSE_CC_BY_4.txt').is_file()
from_source=zipfile.ZipFile(payload/'Application_Source.zip')
for p in source.rglob('*.py'):
    if '__pycache__' in p.parts:continue
    assert from_source.read('race_engineer/'+p.relative_to(source).as_posix())==p.read_bytes(),str(p)
count=0;duration_range=[]
for code in info['voices']:
    clips=list((assets/'clips'/code).glob('*.wav'));assert len(clips)==18,(code,len(clips))
    for p in clips:
        with wave.open(str(p),'rb') as f:
            duration=f.getnframes()/f.getframerate();samples=array.array('h',f.readframes(f.getnframes()))
        assert .05<duration<4.5 and samples and max(map(abs,samples))>60,p
        count+=1;duration_range.append(duration)
print('Version:',info['version'])
print('Source/logo files matched:',len(expected))
print('Embedded application source matched; licensed Pocket assets SHA256 matched')
print('Audible short clips:',count,'duration range',round(min(duration_range),3),round(max(duration_range),3))
