# Windows 0.16 source and package checkpoint — October 31, 2026

- 230 Windows regression checks pass with native Tk enabled and no skips.
- Native integrated checks create all 15 actual pages, render synthetic demo telemetry and exercise 132 lesson views (22 topics × both themes × three window sizes), selection/search/clear, compact stacking and full scrolling.
- All five Settings sections pass in Dark/Light at 1360×900 and 1050×760. All 15 switches retain keyboard/focus/disabled/shared-value and save-callback behavior; DPI indicators scale.
- Help coverage browsing validates exact selected maps. The reproducible audit validates all 417 maps; older official filepath snapshot has 371 exact layout matches, 14 identity reviews, 51 other missing maps, 86 containers and one ambiguous path. This is not live alignment or exhaustive current service coverage.
- LEARN-01/02/04 and UI-16/17 are implemented. LEARN-03 photos, remaining maps/guides, UI-18 onward, actual driver speech/listening and live iRacing acceptance remain open.
- Final x64 installer passed fresh isolated extraction and repair: all 6,973 files matched SHA256, previous runtimes were preserved, launcher checks passed and assembly version is 0.16.0.0.
- Extracted Python passed all 230 checks with zero skips plus the native integrated all-page/132-lesson checks with zero callback errors. See WINDOWS_0_16_INSTALLER.json, WINDOWS_0_16_PACKAGED_TESTS.json and WINDOWS_0_16_PACKAGED_GUI.json.
- Native speech/capture evidence below belongs to the earlier 0.15 checkpoint. No physical-driver or iRacing acceptance is inferred from the UI tests. No public release feed or existing user installation was changed.
- Final verification records accompany the source handoff after the installer is built; the embedded application-source archive contains the build-time source/checklist checkpoint.

## Historical 0.15 Windows speech and delivery evidence

# Windows continuation verification — October 31, 2026

- 208 regression checks pass using the assembled Windows/Python 3.14 runtime.
- Final x64 installer passed isolated installation and repair checks, preserving the prior runtime. All 6,968 extracted files matched their payload SHA256.
- Extracted runtime created all 15 actual Tk pages and rendered synthetic demo data without callback errors; launcher --check passed.
- Pocket generated the controlled speech samples; Vosk recognized Hey Kerby at 16, 44.1 and 48 kHz. The wake gate routed the question and generated the local reply.
- G435 capture delivered 47 blocks at 44.1 kHz; system output stream opened. Live microphone audio was discarded. Actual human speech and headset listening remain unverified.
- Qwen3 0.6B installed and answered on Windows CPU in 3.92 seconds. The answer was generic; this is not quality acceptance.
- Exact Windows dependency URLs/hashes and native result JSON files accompany this source.
- UI-24 and key-field removal are packaged. Other checklist items, simulator telemetry, live acoustic timing, fullscreen/VR and universal coaching coverage remain pending.
- No existing installed app, user history, account settings or public release feed was modified.

## Earlier Linux checkpoint (historical)

# Validation evidence — October 31, 2026

- `PYTHONPATH=race_engineer python3 -m unittest discover -s race_engineer/tests`: **203 tests passed**, Python 3.12/Linux.
- Includes selected microphone capture/local recognition bridge, wake gating, echo/test-mode suppression, local lessons/follow-up, measured/stale-data handling, key-free controller path, download checksum failure and archive traversal rejection.
- Actual local model: pinned Qwen3 0.6B Q8 and llama.cpp b12017 CPU. Download hashes verified; one real Linux response completed in 9.93 s including startup. The response was generic and is not quality acceptance. No hosted API or ChatGPT subscription was used by that inference test.
- Model/runtime download hashes are pinned in `engineer/local_ai_sources.json`. Model Apache-2.0, runtime MIT; notices included.
- No 0.15 Windows installer was assembled in this checkpoint. Windows launch, physical microphone, ASR wake latency, headset voice quality, simulator frame impact, cue acoustic timing, fullscreen/VR and all-car/all-layout coaching remain unverified or incomplete.
- Earlier documents/preview images describe older revisions. The master checklist and WORK_IN_PROGRESS.md take precedence.
