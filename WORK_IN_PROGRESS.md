# KerbSignal secondary work — October 31, 2026

**Status: Secondary work.** This repository contains the secondary Windows/Python work. [Main work: InvectedGaming/KerbSignal](https://github.com/InvectedGaming/KerbSignal).

Current 0.16 work: Settings UI-16/UI-17, 22 complete offline racecraft lessons and diagrams (LEARN-01/02/04; photos in LEARN-03 remain open), strict safe map loading, reproducible TEL-03/04 audit and an in-app Help coverage browser. 230 Windows checks pass with native Tk enabled; integrated all-15-page checks include 132 lesson views at three sizes and both themes. Full text search, repeated selection and compact stacking work. The x64 installer passed fresh extraction and repair (6,973 file hashes), previous-runtime preservation, launcher checks, all 230 extracted-runtime tests and integrated native UI checks. Final verification records accompany docs/VALIDATION.md in the source handoff; the embedded source/checklist is the build-time checkpoint.

Continue from this 0.16 Windows test-build source. Keep the canonical 134-item checklist synchronized; preserve Pit Wall option 1 and left navigation. The user confirmed **fully local and free**: no Codex sign-in, paid API or ChatGPT/Codex allowance.

Earlier 0.15 checkpoint: recovered source; Windows test isolation; 208 passing regression checks; real hidden Tk startup/rendering across 15 pages; native Pocket speech and Vosk recognition; Hey Kerby question routing and generated reply; G435 microphone capture at 44.1 kHz with 47 delivered blocks and system output stream opening; initial conversion import moved before microphone opening so the first words are not discarded. Live microphone audio was never saved.

UI-24 now formats long gaps, next-brake ETA, recap/setup lap times and observation timestamps in minutes, with rounding carried correctly. 153.7s becomes 2:33.7. Signed differences remain seconds.

The optional Qwen3 0.6B model installed and answered on Windows CPU in 3.92 seconds. The answer was generic; model quality is not accepted. Fast racing facts remain bounded by LocalEngineer and matched telemetry. Extended chat pauses while moving and cannot execute code or control the computer.

A native x64 installer is built with build_windows_native.py and verified through an isolated /VERIFY install. User installation, history, account settings and release feed remain untouched. Physical spoken-driver ASR, headset listening, simulator timing/fullscreen/VR and other open checklist rows are not complete. Use docs/BUILD.md and the Windows evidence JSON files.

Next: Windows/iRacing acceptance, then UI-18/19/20 dashboard, input-smoothness and tutorial work, verified track/guide gap closure and the remaining backlog. Do not infer exact-car traits from a brand, official turn numbers from braking-zone order or world-record pace from personal references. Superseded cloud code remains historical and is not imported by app.py.

Source delivery: https://github.com/Kdyanamicstudios/Kerbsignal-2 is the user-selected secondary Windows/Python repository. The existing repository was not modified.
