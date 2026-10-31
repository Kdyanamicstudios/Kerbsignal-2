"""Export a source-only GitHub handoff; never include runtime/user data."""
from pathlib import Path
import ast,hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1]
version=next(ast.literal_eval(node.value) for node in ast.parse((ROOT/'race_engineer/engineer/updater.py').read_text(encoding='utf8')).body
 if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='VERSION' for target in node.targets))
stage=ROOT/'github_handoff/KerbSignal'
assert stage.resolve().is_relative_to(ROOT.resolve()) and stage.name=='KerbSignal'
if stage.exists():shutil.rmtree(stage)
stage.mkdir(parents=True)
for folder in ('race_engineer','windows_build','docs','previews'):
 for p in (ROOT/folder).rglob('*'):
  if not p.is_file():continue
  if p.name.startswith('.'):continue # incomplete hidden download fragments
  rel=p.relative_to(ROOT)
  if 'speech_assets' in rel.parts and p.name!='SOURCES.json':continue
  if any(x in rel.parts for x in ('__pycache__','payload','generated','downloads','tools','vc_runtime','wheels314','neural_wheels','speech_wheels','linux_speech_wheels')):continue
  if p.suffix.lower() in ('.pyc','.exe','.dll','.pyd','.msi','.whl','.gguf','.onnx','.safetensors','.sqlite3','.log','.bin'):continue
  q=stage/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
for name in ('README.md','LICENSE','AGENTS.md','WORK_IN_PROGRESS.md','KerbSignal_Master_Checklist.md','WINDOWS_START_HERE.txt','.gitignore','.gitattributes'):
 shutil.copy2(ROOT/name,stage/name)
for name in ('KerbSignal_New_UI.png','KerbSignal_Pit_Wall_Sidebar_Preview.png','KerbSignal_Startup_Animation.gif','KerbSignal_Startup_Animation.mp4'):
 p=ROOT/name
 if p.exists():
  q=stage/'previews'/name;q.parent.mkdir(exist_ok=True);shutil.copy2(p,q)
files=[]
binary_ext={'.png','.wav','.gif','.mp4','.gz','.zip','.ico','.pdf','.jpg','.jpeg','.woff2','.rtf'}
for p in sorted(stage.rglob('*')):
 if not p.is_file():continue
 assert p.stat().st_size<25*1024*1024,str(p)
 assert p.name not in ('auth.json','credentials.json','.env'),str(p)
 data=p.read_bytes()
 if p.suffix.lower() not in binary_ext and b'\0' not in data:
  try:data.decode('utf8')
  except UnicodeDecodeError:pass
  else:
   data=data.replace(b'\r\n',b'\n')
   if p.suffix.lower() in ('.ps1','.bat'):data=data.replace(b'\n',b'\r\n')
   p.write_bytes(data)
 files.append({'path':p.relative_to(stage).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(stage/'FILE_MANIFEST.json').write_text(json.dumps({'version':version+'-windows-test-source','files':files},indent=2)+'\n',encoding='utf8',newline='\n')
archive=ROOT/'KerbSignal_GitHub_Ready.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(stage.rglob('*')):
  if p.is_file():z.write(p,str(p.relative_to(stage.parent)))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for item in files:assert hashlib.sha256(z.read('KerbSignal/'+item['path'])).hexdigest()==item['sha256']
 required=['README.md','.gitignore','LICENSE','race_engineer/app.py','race_engineer/engineer/local_ai.py','race_engineer/tests/test_local_engineer.py','windows_build/RaceEngineer.nsi','docs/BUILD.md','KerbSignal_Master_Checklist.md']
 for name in required:assert 'KerbSignal/'+name in z.namelist(),name
 assert z.read('KerbSignal/race_engineer/MASTER_CHECKLIST.md')==z.read('KerbSignal/KerbSignal_Master_Checklist.md')
print(json.dumps({'archive':str(archive),'files':len(files)+1,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},indent=2))
