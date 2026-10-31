# Windows 0.16 build and recovery

A single **x64 Windows 0.16 test installer** is built by `windows_build/build_windows_native.py`. It includes the Settings/switch redesign, 22 offline lessons/diagrams and coverage browser plus the earlier local speech/chat and minute-format fixes. It is not a claim that every open checklist requirement is complete.

## Build with a recovered runtime

1. Run the supplied 0.16 EXE with `/VERIFY /D=C:\absolute\workspace\runtime-check`. This extracts to the explicitly supplied folder without shortcuts or launch.
2. Read `current.ini` there. Copy its `versions/<Version>` folder into `windows_build/payload` in this checkout. Runtime binaries and large speech models intentionally stay out of Git.
3. With Windows x64 and .NET Framework available, run `python windows_build/build_windows_native.py`. It updates the payload with this checkout's source and generates `KerbSignal_0.16.exe`. No NSIS compiler, API key or hosted model is needed.
4. Run `python windows_build/verify_windows_native.py --installer KerbSignal_0.16.exe --target C:\absolute\workspace\fresh-0-16-check` with a fresh target. This checks extraction, repair, prior-runtime preservation, launcher health and per-file SHA256. Run the regression suite with the extracted runtime's Python. Exercise real Tk, recognition, selected microphone, headset playback and iRacing separately.

The installer hashes its embedded ZIP before extracting. Each installation or repair gets a fresh version folder; previous runtimes and user data remain intact. The new launcher and current-version pointer are replaced only after extraction succeeds. Normal installation adds KerbSignal shortcuts and opens the app. Verification mode creates neither shortcuts nor a running app.

`NativeInstaller.cs` and `NativeLauncher.cs` are included under the existing project licence. The build uses the system x64 C# compiler. NSIS scripts remain historical tooling; their 32-bit compiler could not start in this execution environment.

## Verified local assets

Vosk 0.3.45 and the small US-English model are bundled; the model and Pocket TTS files are checked against the pinned SOURCES.json manifests. Exact additional Windows package versions, URLs and hashes are in SPEECH_DEPENDENCIES.json. The optional Qwen model/runtime is installed by the app when requested and is not bundled into the EXE. Its pinned downloads and CPU inference were exercised on Windows.

Earlier 0.14 recovery helpers and audit files are historical. Do not run build_checklist.py over the canonical hand-edited checklist. Do not publish or change the private release feed as part of a local build.

The builder reads engineer/updater.py for the version and updates installer/launcher metadata and BUILD_INFO.json together. No release feed is published by this build.
