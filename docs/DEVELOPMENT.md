# Developer setup

Use Python 3.12 for the documented regression command. Native GUI development requires Tcl/Tk. Windows is required for actual iRacing shared-memory, HID/microphone, overlay and playback acceptance.

From the repository root:

```sh
python -m venv .venv
# Activate .venv with the command for your OS, then:
python -m pip install -r race_engineer/requirements.txt
PYTHONPATH=race_engineer python -m unittest discover -s race_engineer/tests
```

PowerShell equivalent for the last command:

```powershell
$env:PYTHONPATH = "race_engineer"
python -m unittest discover -s race_engineer/tests
```

`python race_engineer/app.py` launches the source UI. Fully functional speech needs the runtime/model assets described in BUILD.md, with models copied to the paths expected by the app. A clean source checkout does not include those large models. Most hardware integrations load lazily; absence of audio models is not evidence that the app's microphone is fixed. Use the shipped 0.14 runtime for development recovery where available.

`RACE_ENGINEER_DATA` may point to a disposable development-data directory. Keep personal telemetry outside the repository. The original data directory name is retained for compatibility. `engineer/local_ai_sources.json` pins the free model and CPU runtimes; the app installs these in user data only after the user requests it. `local_ai.py` and `local_engineer.py` are new and need Windows review. The historical remote voice implementation is not imported by the current app.
