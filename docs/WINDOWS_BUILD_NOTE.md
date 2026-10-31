# Windows 0.15 local continuation

Recovered source and the existing Windows 0.12 Python 3.14 runtime were assembled into a new 0.15 test build. Vosk and its dependencies were installed into isolated workspace staging; exact package URLs and hashes are recorded in SPEECH_DEPENDENCIES.json. Speech and Pocket model files were restored against their existing pinned manifests. The optional Qwen chat model is not bundled; the in-app installation flow was exercised on Windows.

The native hidden Tk application created all 15 pages and rendered synthetic demo data without callback errors. Pocket generated both recognition test phrases; Vosk decoded them on Windows. Default G435 capture and system output streams opened; a separate capture check confirmed PCM delivery. Live microphone audio was discarded. The model answered on CPU in 3.92 seconds; that answer was generic, so model quality remains unaccepted.

Timer display now carries correctly at minute boundaries, including 153.7s to 2:33.7. Signed gain and delta values retain seconds.

No existing user installation, history, cloud settings or public release feed was modified. The installer supports /VERIFY /D=an-isolated-workspace-directory for extraction checks without shortcuts or launch. Human speech, headset listening, iRacing shared memory and acoustic cue timing remain acceptance work. This test build does not complete the other open checklist requirements.
