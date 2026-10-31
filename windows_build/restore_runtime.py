"""Developer utility: restore the bundled runtime from a prior release installer.
Usage: python restore_runtime.py /path/RaceEngineer.exe /path/7zz
The source bundle contains the installer. Use an official 7-Zip binary.
"""
from pathlib import Path
import shutil,subprocess,sys,tempfile
root=Path(__file__).resolve().parent
if len(sys.argv)!=3:raise SystemExit(__doc__)
installer=Path(sys.argv[1]).resolve();seven=Path(sys.argv[2]).resolve()
with tempfile.TemporaryDirectory() as folder:
 subprocess.run([str(seven),'x',str(installer),'-o'+folder,'-y'],check=True)
 candidates=list(Path(folder).rglob('pythonw.exe'))
 if len(candidates)!=1:raise ValueError('Expected one bundled runtime')
 source=candidates[0].parent
 if not (source/'python314.dll').exists():raise ValueError('Python 3.14 runtime not found')
 shutil.copytree(source,root/'payload',dirs_exist_ok=True)
 assets=root/'neural_assets';shutil.copytree(source/'engineer/neural_assets',assets,dirs_exist_ok=True)
 print('Runtime restored. Review source, then run assemble_payload.py and compile Launcher.nsi / RaceEngineer.nsi.')
