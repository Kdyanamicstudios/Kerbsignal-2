# KerbSignal — Secondary work

**Status: Secondary work.** This repository contains the secondary Windows/Python work. [Main work: InvectedGaming/KerbSignal](https://github.com/InvectedGaming/KerbSignal).

Windows iRacing race engineer, local telemetry coach and driving-review app.

**Windows/Python snapshot: 0.16 test build.** Includes redesigned Settings and On/Off controls, 22 complete offline lessons with annotated diagrams, a searchable track-coverage browser, and the earlier local engineer/speech/minute-format work. Other checklist features remain incomplete. The built EXE is distributed separately from repository source.

Start with [the development handoff](WORK_IN_PROGRESS.md) and [the full requirements checklist](KerbSignal_Master_Checklist.md). The checklist includes the latest screenshot findings, exact-turn labels, minute formatting and zero-cost local-chat requirement.

Current native Windows screens: [Settings](previews/0.16_Settings_Dark.png), [Racecraft](previews/0.16_Racecraft.png), [Track coverage](previews/0.16_Track_Coverage.png).

## Included

- `race_engineer/`: native Tk app, local telemetry/cue logic, maps, icons, assets, original documentation and regression tests.
- `windows_build/`: native x64 installer sources, runtime recovery/build scripts, legacy NSIS tooling, asset provenance, 90 cached speech clips, third-party notices and corresponding source archives.
- `previews/`: existing design renders and startup animation, for context; previews are not proof of current feature completion.
- `docs/`: developer setup, build/recovery notes, GitHub upload steps and verification evidence.
- `.gitignore`, `.gitattributes`, `LICENSE`, `FILE_MANIFEST.json`: repository hygiene, original GPLv3-or-later licence and per-file integrity manifest.

## Current verification

All 15 native pages and 132 lesson views were exercised in both themes and compact sizes. [Track coverage audit](docs/TRACK_COVERAGE.md): all 417 maps validate; 371 match exact layout paths in the official article snapshot, 14 need identity review and 51 are missing. The article is older than the audit and does not prove complete current service coverage. Licensed racing photos and live iRacing/driver acceptance remain open.

230 automated tests passed with the Windows/Python 3.14 packaged runtime. Qwen3 0.6B local inference was also exercised on Windows CPU. Native GUI and microphone capture were checked; live-driver/iRacing acceptance and free-model response quality remain open. The 0.16 x64 installer passed isolated extraction/repair, all 6,973 file hashes, prior-runtime preservation and extracted-runtime/native UI checks. Read `docs/VALIDATION.md` for limits.

## Free chat

The new chat path runs locally and requires no account, API key or ChatGPT/Codex allowance. Optional extended chat has a one-time free model/runtime download of about 632 MiB. It is a small local model, not this hosted Codex conversation or a coding agent. Fast racing answers use local lessons/telemetry; driving cues remain independent. See the checklist for uncompleted work.

Repository: [Kdyanamicstudios/Kerbsignal-2](https://github.com/Kdyanamicstudios/Kerbsignal-2).

## Colleague setup

See [DEVELOPMENT.md](docs/DEVELOPMENT.md), [BUILD.md](docs/BUILD.md) and [GITHUB_UPLOAD.md](docs/GITHUB_UPLOAD.md). The user is not expected to perform developer setup.

No credentials, personal lap database, downloaded model weights, Windows runtime, installer EXE or previous Git history are in this repository. These are deliberately separate from source; asset URLs/hashes and existing restore scripts are retained. A native x64 0.16 test installer is available separately. See docs/BUILD.md for verified runtime extraction and rebuilding; a clean from-scratch dependency bootstrap is not yet complete.

## Licence

Original application licence is GNU GPL version 3 or later, retained without relicensing. Third-party components keep their respective licences and attributions under `windows_build/third_party` and `race_engineer/THIRD_PARTY_NOTICES.txt`.
