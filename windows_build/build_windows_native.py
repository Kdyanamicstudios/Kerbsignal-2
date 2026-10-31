"""Build a single x64 EXE using Windows' .NET compiler and a staged runtime.

No installed app or user data is modified. Run the generated EXE with
/VERIFY /D=an-absolute-workspace-path to validate extraction without shortcuts.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile

build=Path(__file__).resolve().parent
root=build.parent;source=root/'race_engineer';payload=build/'payload'
csc=Path('C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe')
assert csc.is_file(),'Windows .NET Framework x64 compiler required'
assert (payload/'pythonw.exe').is_file(),'Restore/stage the Windows runtime first'
shutil.copy2(source/'app.py',payload/'app.py')
shutil.copytree(source/'engineer',payload/'engineer',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
shutil.copy2(source/'MASTER_CHECKLIST.md',payload/'MASTER_CHECKLIST.md')
with zipfile.ZipFile(payload/'Application_Source.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for p in sorted(source.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.pyc':continue
        if 'speech_assets' in p.parts and p.name!='SOURCES.json':continue
        archive.write(p,'race_engineer/'+p.relative_to(source).as_posix())
    for p in sorted(build.iterdir()):
        if p.is_file() and p.suffix in ('.py','.cs','.nsi','.ico'):archive.write(p,'windows_build/'+p.name)
    for p in sorted((root/'docs').rglob('*')):
        if p.is_file() and p.name!='WINDOWS_PACKAGE.json':archive.write(p,'docs/'+p.relative_to(root/'docs').as_posix())
    for name in ('AGENTS.md','README.md','LICENSE','WORK_IN_PROGRESS.md'):
        archive.write(root/name,name)

archive_path=root/'KerbSignal_Payload.zip'
with zipfile.ZipFile(archive_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for p in sorted(payload.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':archive.write(p,p.relative_to(payload).as_posix())
with archive_path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
print('Payload ZIP prepared:',archive_path.stat().st_size,flush=True)
generated=build/'generated';generated.mkdir(exist_ok=True)
launcher=generated/'KerbSignalLauncher.exe'
installer_source=generated/'NativeInstaller.cs'
installer_source.write_text((build/'NativeInstaller.cs').read_text().replace('__PAYLOAD_SHA256__',digest),encoding='utf8')
common=[str(csc),'/nologo','/target:winexe','/platform:x64','/optimize+',
    '/reference:System.Windows.Forms.dll','/reference:System.Drawing.dll','/win32icon:'+str(build/'raceengineer.ico')]
subprocess.run(common+['/out:'+str(launcher),str(build/'NativeLauncher.cs')],check=True)
installer=root/'KerbSignal_0.15.exe'
subprocess.run(common+['/reference:System.IO.Compression.dll','/reference:System.IO.Compression.FileSystem.dll',
    '/resource:'+str(archive_path)+',KerbSignal.Payload.zip','/resource:'+str(launcher)+',KerbSignal.Launcher.exe',
    '/out:'+str(installer),str(installer_source)],check=True)
with installer.open('rb') as stream:installer_hash=hashlib.file_digest(stream,'sha256').hexdigest()
result=dict(version='0.15.0',architecture='x64',payload_sha256=digest,installer_sha256=installer_hash,bytes=installer.stat().st_size)
(root/'docs/WINDOWS_PACKAGE.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
