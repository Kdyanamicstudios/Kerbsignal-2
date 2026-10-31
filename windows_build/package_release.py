from pathlib import Path
import hashlib,json,zipfile,subprocess,sys
root=Path(__file__).resolve().parent.parent;build=root/'windows_build';exe=root/'KerbSignal.exe'
sys.path.insert(0,str(build.parent/'build_tools/pe_tools'))
import pefile
for file in (exe,build/'LaunchRaceEngineer.exe'):
 pe=pefile.PE(str(file));assert pe.VS_FIXEDFILEINFO[0].FileVersionMS==(12),str(file)
 assert pe.VS_FIXEDFILEINFO[0].FileVersionLS==0,str(file)
 pe.close()
r=subprocess.run([str(root/'build_tools/7zz'),'t',str(exe)],capture_output=True,text=True)
assert r.returncode==0,r.stdout+r.stderr
print('Installer archive integrity and PE version verified.',flush=True)
sha=hashlib.sha256(exe.read_bytes()).hexdigest()
record=dict(version='0.12.0',exe_bytes=exe.stat().st_size,exe_sha256=sha,automated_tests=136,native_runtime_binaries_verified=88,windows_iracing_live_tested=False,update_channel_configured=False)
(build/'release_012.json').write_text(json.dumps(record,indent=2))
zip_path=root/'KerbSignal_Windows.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 z.write(exe,'KerbSignal.exe')
 z.write(root/'WINDOWS_START_HERE.txt','START_HERE.txt')
 z.write(root/'release09/COACHING_VIDEO_SOURCES.md','COACHING_VIDEO_SOURCES.md')
 z.write(build/'payload/BUILD_INFO.json','BUILD_INFO.json')
 z.write(build/'release_012.json','RELEASE_CHECKS.json')
 z.writestr('CHECKSUMS.sha256',sha+'  KerbSignal.exe\n')
 for p in (root/'race_engineer').rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':z.write(p,'Source/race_engineer/'+str(p.relative_to(root/'race_engineer')))
 for name in ('assemble_payload.py','render_neural_clips.py','verify_payload.py','RaceEngineer.nsi','Launcher.nsi','raceengineer.ico','restore_runtime.py','package_release.py','build_map_catalogue.py'):
  z.write(build/name,'Source/windows_build/'+name)
 for p in (build/'payload/Third_Party').rglob('*'):
  if p.is_file() and not any(part.startswith('.') for part in p.relative_to(build/'payload/Third_Party').parts):z.write(p,'Third_Party/'+str(p.relative_to(build/'payload/Third_Party')))
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 assert hashlib.sha256(z.read('KerbSignal.exe')).hexdigest()==sha
 assert z.read('Source/race_engineer/app.py')==(root/'race_engineer/app.py').read_bytes()
record['zip_bytes']=zip_path.stat().st_size
(build/'release_012.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record),flush=True)
