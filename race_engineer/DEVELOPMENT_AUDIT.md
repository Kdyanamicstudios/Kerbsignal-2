# KerbSignal 0.13 Windows test-build audit

A new 0.13 Windows test installer accompanies this checkpoint. It contains the rebuilt native driving screen. Native Windows/iRacing hardware and audio timing validation remains pending; installing it is necessary to see these changes in place of 0.12.

| Request | Applied work | Validation / remaining limits |
|---|---|---|
| Redesigned UI and tabs | New fixed left rail, full-width native driving canvas, timing strip, engineer banner, circuit/G-force row and telemetry graph | Production painter rendered in dark/light/offline states; five window-size bounds checks; native Windows visual QA pending |
| Settings tab | SETTINGS is now a first-level label; general, audio/mic, overlay, devices and update controls | Navigation and persistence tests |
| Startup animation / logo | New racing-kerb/radio mark, Windows ICO, PNG sizes; native 1.4-second startup animation with Escape skip | Asset inspection and source checks; actual Windows display still pending |
| Connected state | Connect button becomes “iRacing connected” only with valid fresh LIVE metadata; stale/demo states separate | Fresh/stale/missing metadata tests |
| Mouse-wheel scrolling | One pointer-aware router handles labels/controls; preserves native text/table scrolling; prevents accidental combobox changes | Child-widget, high-resolution wheel and native-control tests; physical wheel test pending |
| G-force circle | Dedicated large G-FORCE panel beside the circuit map; 3 g circle, lateral/longitudinal values, resultant and recent trace; compact overlay retained | Main circle at least 136 px diameter at tested sizes; stays visible offline; SDK/wall-clock stale data clears the live dot; overlay 160 × 80 bounds checked |
| Smaller overlay | Widths from 160 px; click-through, opacity and placement retained | Size persistence and rendering tests |
| Better free speech | Five local Supertonic 3 male presets added; American/British Kokoro retained | 126 cached driving/spotter WAVs validated for signal and duration; model benchmark and previews produced |
| ElevenLabs research | Official free allowance reviewed; free local engine selected to avoid a required account/quota | No ElevenLabs account or subscription was created; voice remains synthetic |
| Australian male voice | Online Australian style request remains available | A verified redistributable recorded Australian male pack remains unsourced; new presets are not falsely labeled Australian |
| Vocabulary / chattiness | Quiet/Standard/Chatty setting; varied input/straight/pit phrases; information tied to telemetry events | No idle chatter loop; critical calls retain priority |
| Pit-stop detection | Pit-road entry, confirmed stationary box, service-state edges/corrections, exit | Drive-through/trackside/stale-service tests; real car pit channels still need live validation |
| Pit recap | Session type, recorded pace, available position, fuel estimate only with measured consumption, reported tires, next experiment/why | Saved to session history; service requests never treated as completed work |
| Practice / qualifying / race | SDK metadata normalized and shown; pit briefings adapt to session type | Mode and controller integration tests |
| Live coaching, mph and timers | All-car/layout SDK identity, speed in mph, live timer, brake/turn/throttle phases retained | Positioned instructions need matched reference or authored guide; timing must be checked on real hardware |
| Braking / steering analysis | Bounded meter/percentage-point advice and wheel-angle comparison | Reference-relative, similar-speed gates; wheel angle alone is not a balance diagnosis |
| Actual maps / GPS | 417 sourced layout maps and observed-route fallback; live GPS preferred, projection labeled | Not guaranteed coverage of every current/future layout; no optimal-line claim |
| Racecraft library | 22 searchable original lessons, exercises, official learning links | Includes drafting, controlled passes/dive-bomb avoidance, weight transfer and string analogy |
| Session recap / WHY | Persistent history, corner priorities, input-event observations, tire/pit reports and practice explanations | Heuristics and possible explanations are clearly distinguished from measured facts |
| Opponent analysis | Repeated section-pace comparisons and conditional passing opportunities | No opponent pedal/steering data; no guaranteed clear passing lane |
| Praise loop | Clean-lap milestones, deduplication and minimum intervals retained | Existing regression checks |
| Microphone / devices | Selected mic, gain, local meter/recognition test; controller enumeration/manual roles | Native Windows English recognizer and physical hardware test pending |
| Setup, YouTube, voice commands | Controlled setup experiments, YouTube browser launch, local command grammar retained | Does not automatically change the car’s setup or drive controls |
| Better reference workflow | Native IBT importer validates complete clean laps and recorded SDK identity/time; CSV timing explicitly estimated | No universal licensed expert-lap catalogue; Garage61 access remains user/team/provider dependent |
| In-app updating | Verified resumable chunks, progress/cancel, startup check preference, stop-before-install behavior | Release host is deployed privately; anonymous native downloads need explicit authorization for public read access |

## Three verification passes

1. Requirement audit: this table records implementation and outstanding limits.
2. Automated flow/data checks: 176 tests passed after the latest pit and UI integrations.
3. Asset/build checks: all 126 short WAVs have audible signal and valid durations; model assets are pinned/checksummed; existing 88 native runtime binaries resolve. Native Windows visual, microphone, wheel and acoustic-latency checks remain unverified.

The installer is explicitly a Windows test build, not a claim of live Windows/iRacing validation. The stable 0.12 files are retained separately. No feature is represented as a recorded human engineer or a globally optimal reference. In-app updates still await release-feed access authorization.

## Trophi.ai design request

The prior feature review remains available in FEATURE_REVIEW.md. Current web lookup calls failed and a direct request to the public site returned HTTP 403, so the current visual design could not be verified. This layout is original and must not be described as a verified reproduction of Trophi.ai. The exported UI image uses illustrative telemetry, the production Drive painter and a depiction of the native navigation/header; it is not a Windows screenshot.
