import os,subprocess,shutil,zipfile,json,hashlib,re,sys
from pathlib import Path
root=Path(__file__).resolve().parent;source=root.parent/'race_engineer';payload=root/'payload'
sys.path.insert(0,str(source))
from engineer.neural_voice import VOICES
voice_ids=[v[0] for v in VOICES.values()]
payload.mkdir(exist_ok=True)
version=(root/'runtime_version.txt').read_text().strip() if (root/'runtime_version.txt').exists() else '3.14.10'
previous=json.loads((payload/'BUILD_INFO.json').read_text()) if (payload/'BUILD_INFO.json').exists() else {}
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(root/'tools/usr/lib/x86_64-linux-gnu')
for name in ('core.msi','exe.msi','lib.msi','tcltk.msi') if (root/'downloads'/version/'core.msi').exists() else ():
 result=subprocess.run([str(root/'tools/usr/bin/msiextract'),'-C',str(payload),str(root/'downloads'/version/name)],env=env,capture_output=True,text=True)
 if result.returncode:raise RuntimeError(result.stderr)
 print('Extracted',name,flush=True)
for dll in (root/'vc_runtime').glob('*.dll'):
 shutil.copy2(dll,payload/dll.name)
site=payload/'Lib/site-packages';site.mkdir(exist_ok=True)
wheels=[]
for wheel in sorted(set((root/'wheels314').glob('*.whl'))|set((root/'neural_wheels').glob('*.whl'))|set((root/'speech_wheels').glob('*.whl'))):
 with zipfile.ZipFile(wheel) as z:
  for name in z.namelist():
   if not (site/name).resolve().is_relative_to(site.resolve()):raise ValueError('Bad wheel path')
  z.extractall(site)
 wheels.append(dict(file=wheel.name,sha256=hashlib.sha256(wheel.read_bytes()).hexdigest()))
 print('Bundled',wheel.name,flush=True)
if not wheels:wheels=previous.get('wheels',[])
else:
 known={item['file']:item for item in previous.get('wheels',[])}
 known.update({item['file']:item for item in wheels});wheels=list(known.values())
shutil.copy2(source/'app.py',payload/'app.py')
shutil.copy2(root/'raceengineer.ico',payload/'app.ico')
shutil.copytree(source/'engineer',payload/'engineer',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
speech_source=root/'speech_assets';speech_target=payload/'engineer/speech_assets'
speech_manifest=json.loads((speech_source/'SOURCES.json').read_text())
if speech_target.exists():shutil.rmtree(speech_target)
for item in speech_manifest['files']:
 p=speech_source/item['file']
 if not p.resolve().is_relative_to(speech_source.resolve()):raise ValueError('Unsafe speech model path')
 if p.stat().st_size!=item['size'] or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Speech model verification failed')
 q=speech_target/item['file'];q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
shutil.copy2(speech_source/'SOURCES.json',speech_target/'SOURCES.json')
assets=payload/'engineer/neural_assets';assets.mkdir(parents=True,exist_ok=True)
shutil.copy2(root/'neural_assets/kokoro-v1.0.int8.onnx',assets/'kokoro-v1.0.int8.onnx')
shutil.copy2(root/'neural_assets/voices-v1.0.bin',assets/'voices-v1.0.bin')
if (assets/'clips').exists():shutil.rmtree(assets/'clips')
for code in voice_ids:shutil.copytree(root/'neural_assets/clips'/code,assets/'clips'/code)
# Retire the rejected voice models from generated staging. User data is separate.
if (assets/'supertonic').exists():shutil.rmtree(assets/'supertonic')
pack_source=root/'neural_assets/pocket';pack_manifest=json.loads((pack_source/'SOURCES.json').read_text());pack_target=assets/'pocket'
if pack_target.exists():shutil.rmtree(pack_target)
pack_target.mkdir()
for item in pack_manifest['files']:
 p=pack_source/item['file']
 if not p.resolve().is_relative_to(pack_source.resolve()):raise ValueError('Unsafe model asset path')
 if p.stat().st_size!=item['size'] or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Model asset verification failed: '+item['file'])
 q=pack_target/item['file'];q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
shutil.copy2(pack_source/'SOURCES.json',pack_target/'SOURCES.json')
if (root/'third_party').exists():shutil.copytree(root/'third_party',payload/'Third_Party',dirs_exist_ok=True)
shutil.copy2(source/'LICENSE.txt',payload/'LICENSE.txt')
shutil.copy2(source/'THIRD_PARTY_NOTICES.txt',payload/'THIRD_PARTY_NOTICES.txt')
shutil.copy2(source/'MASTER_CHECKLIST.md',payload/'MASTER_CHECKLIST.md')
shutil.copy2(root.parent/'WINDOWS_START_HERE.txt',payload/'START_HERE.txt')
# Corresponding application source remains available inside the standalone EXE.
with zipfile.ZipFile(payload/'Application_Source.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in source.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':z.write(p,'race_engineer/'+str(p.relative_to(source)))
 for name in ('assemble_payload.py','render_neural_clips.py','verify_payload.py','RaceEngineer.nsi','Launcher.nsi','raceengineer.ico','restore_runtime.py'):
  z.write(root/name,'windows_build/'+name)
(payload/'launch.pyw').write_text('''import os,sys,traceback,ctypes\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parent))\ntry:\n    user32=ctypes.windll.user32\n    kernel=ctypes.windll.kernel32\n    kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p]\n    kernel.CreateMutexW.restype=ctypes.c_void_p\n    app_mutex=kernel.CreateMutexW(None,False,'Local\\\\RaceEngineerApp')\n    if not app_mutex:raise OSError('Could not create application mutex')\n    if kernel.GetLastError()==183:\n        user32.MessageBoxW(None,'KerbSignal is already running. Open its existing window.','Race Engineer',0x40)\n        sys.exit(0)\n    import app\n    root=app.tk.Tk()\n    root.iconbitmap(default=str(Path(__file__).resolve().parent/'app.ico'))\n    application=app.App(root)\n    root.mainloop()\nexcept Exception:\n    error=traceback.format_exc()\n    folder=Path(os.environ.get("LOCALAPPDATA",str(Path.home())))/"RaceEngineer"\n    folder.mkdir(parents=True,exist_ok=True)\n    (folder/"startup_error.log").write_text(error,encoding="utf-8")\n    ctypes.windll.user32.MessageBoxW(None,"KerbSignal could not start. Details were saved to "+str(folder/"startup_error.log"),"Race Engineer",0x10)\n    sys.exit(1)\n''',encoding='utf-8')
manifest=dict(product='KerbSignal',version='0.15.0',python=version,platform='Windows x64',wheels=wheels,
 voices=voice_ids,voice_telemetry=False,
 assets=[dict(file=str(p.relative_to(assets)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in assets.rglob('*') if p.is_file()],
 scripts=[p.name for p in (payload/'engineer').glob('*.ps1')])
# Restored payloads can contain interrupted-transfer fragments beside complete
# files. Only generated staging is cleaned, and only when the real sibling is
# present. These fragments are never runtime dependencies.
fragment=re.compile(r'\.(?P<base>.+\.(?:onnx|dll|pyd|exe|bin|zip|msi))\.[A-Za-z0-9]{6,10}(?:\.[A-Za-z0-9]{6,10})?$')
discarded=[]
for p in payload.rglob('*'):
 if not p.is_file():continue
 match=fragment.fullmatch(p.name)
 if match and (p.parent/match['base']).is_file():discarded.append((p,p.stat().st_size))
for p,size in discarded:p.unlink()
manifest['assets']=[dict(file=str(p.relative_to(assets)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in assets.rglob('*') if p.is_file()]
print('Discarded redundant staged bytes:',sum(size for p,size in discarded),flush=True)
(payload/'BUILD_INFO.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
required=['pythonw.exe','python.exe','python314.dll','vcruntime140.dll','vcruntime140_1.dll','msvcp140.dll','msvcp140_1.dll','Lib/tkinter/__init__.py','Lib/sqlite3/__init__.py','DLLs/_tkinter.pyd','DLLs/_ssl.pyd','DLLs/_sqlite3.pyd','Lib/site-packages/websocket/__init__.py','Lib/site-packages/sounddevice.py']
for name in required:
 if not (payload/name).is_file():raise RuntimeError('Missing '+name)
assert list(site.rglob('*portaudio*.dll')),'PortAudio DLL missing'
assert (site/'espeakng_loader/espeak-ng.dll').is_file(),'Offline phonemizer DLL missing'
assert list((site/'onnxruntime').rglob('*.pyd')),'Offline speech runtime missing'
print('Payload verified:',sum(p.stat().st_size for p in payload.rglob('*') if p.is_file()),'bytes',flush=True)
