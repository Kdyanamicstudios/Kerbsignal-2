"""Save reproducible source and approved small assets, excluding runtime weights."""
from pathlib import Path
import json
import os
import zipfile
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"race_engineer"))
from engineer.neural_voice import VOICES
voice_ids={v[0] for v in VOICES.values()}

root=Path(__file__).resolve().parents[1]
archive=root/'KerbSignal_Development_0.13.zip'
temporary=archive.with_suffix('.zip.next')
with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as out:
    def put(p,name):out.write(p,name)
    for p in (root/'race_engineer').rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
            put(p,'Source/'+str(p.relative_to(root)))
    for p in (root/'windows_build').iterdir():
        if p.is_file() and (p.suffix in ('.py','.nsi','.ico') or p.name in ('DEVELOPMENT_CHECKS.json','VOICE_CLIP_CHECKS.json','MICROPHONE_CHECKS.json','runtime_version.txt')):
            put(p,'Source/'+str(p.relative_to(root)))
    for p in (root/'windows_build/neural_assets/clips').rglob('*.wav'):
        if p.parent.name in voice_ids:put(p,'Source/'+str(p.relative_to(root)))
    model=root/'windows_build/neural_assets/pocket'
    manifest=json.loads((model/'SOURCES.json').read_text())
    put(model/'SOURCES.json','Source/windows_build/neural_assets/pocket/SOURCES.json')
    for item in manifest['files']:
        p=model/item['file']
        if p.is_file() and p.stat().st_size<1048576:put(p,'Source/'+str(p.relative_to(root)))
    speech=root/'windows_build/speech_assets'
    if (speech/'SOURCES.json').exists():
        put(speech/'SOURCES.json','Source/windows_build/speech_assets/SOURCES.json')
        for p in speech.rglob('*'):
            if p.is_file() and p.name!='SOURCES.json' and p.stat().st_size<262144:put(p,'Source/'+str(p.relative_to(root)))
    for p in (root/'windows_build/third_party').rglob('*'):
        if p.is_file():put(p,'Third_Party/'+str(p.relative_to(root/'windows_build/third_party')))
    put(root/'WINDOWS_START_HERE.txt','Source/WINDOWS_START_HERE.txt')
    put(root/'AGENTS.md','Source/AGENTS.md')
    for name in ('README.md','LICENSE','.gitignore','.gitattributes'):
        put(root/name,'Source/'+name)
    for p in (root/'docs').rglob('*'):
        if p.is_file():put(p,'Source/'+str(p.relative_to(root)))
    put(root/'KerbSignal_Master_Checklist.md','KerbSignal_Master_Checklist.md')
    put(root/'WORK_IN_PROGRESS.md','WORK_IN_PROGRESS.md')
    put(root/'KerbSignal_New_UI.png','Preview/KerbSignal_New_UI.png')
    sidebar_preview=root/'KerbSignal_Pit_Wall_Sidebar_Preview.png'
    if sidebar_preview.exists():put(sidebar_preview,'Preview/KerbSignal_Pit_Wall_Sidebar_Preview.png')
    for name in ('KerbSignal_Startup_Animation.gif','KerbSignal_Startup_Animation.mp4'):
        if (root/name).exists():put(root/name,'Preview/'+name)
    out.writestr('README_DEVELOPMENT.txt','KerbSignal 0.15 WORKING SOURCE checkpoint. Latest delivered executable remains 0.14. Key-free local chat and Hey Kerby source added. Microphone capture and bundled local recognition have been reworked; selected device, meter and recognized transcript now share an audio stream. 203 tests passed and actual recorded-speech decoding succeeded. Native Windows/physical microphone validation and 0.15 packaging remain pending. Read the current master checklist before more work. Full Pocket and Vosk model/runtime assets are excluded from this source checkpoint; pinned source hashes/restore scripts are included. The user is not expected to build anything.\n')
os.replace(temporary,archive)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name in ('app.py','engineer/drive_workspace.py','tests/test_drive_workspace.py'):
        assert z.read('Source/race_engineer/'+name)==(root/'race_engineer'/name).read_bytes()
print('Source checkpoint verified:',archive.stat().st_size,'bytes')
