# KerbSignal continuation — October 31, 2026

Continue from this 0.15 Windows test-build source. Keep the canonical 134-item checklist synchronized; preserve Pit Wall option 1 and left navigation. The user confirmed **fully local and free**: no Codex sign-in, paid API or ChatGPT/Codex allowance.

Completed in this continuation: recovered source; Windows test isolation; 208 passing regression checks; real hidden Tk startup/rendering across 15 pages; native Pocket speech and Vosk recognition; Hey Kerby question routing and generated reply; G435 microphone capture at 44.1 kHz with 47 delivered blocks and system output stream opening; initial conversion import moved before microphone opening so the first words are not discarded. Live microphone audio was never saved.

UI-24 now formats long gaps, next-brake ETA, recap/setup lap times and observation timestamps in minutes, with rounding carried correctly. 153.7s becomes 2:33.7. Signed differences remain seconds.

The optional Qwen3 0.6B model installed and answered on Windows CPU in 3.92 seconds. The answer was generic; model quality is not accepted. Fast racing facts remain bounded by LocalEngineer and matched telemetry. Extended chat pauses while moving and cannot execute code or control the computer.

A native x64 installer is built with build_windows_native.py and verified through an isolated /VERIFY install. User installation, history, account settings and release feed remain untouched. Physical spoken-driver ASR, headset listening, simulator timing/fullscreen/VR and other open checklist rows are not complete. Use docs/BUILD.md and the Windows evidence JSON files.

Next: user-facing Windows/iRacing acceptance of this test build, then track/layout coverage audit, UI-16–23 and remaining backlog. Do not infer exact-car traits from a brand, official turn numbers from braking-zone order or world-record pace from personal references. Superseded cloud code remains historical and is not imported by app.py.

Source delivery: https://github.com/Kdyanamicstudios/Kerbsignal-2 is the user-selected separate Windows/Python repository. The existing repository was not modified.
