# KerbSignal — master requirements checklist

Owner: Rakiem Eddy. Canonical selection: **Pit Wall, option 1, with navigation down the left side.**

Updated: October 31, 2026. This is the working checklist for the app, not a claim that every requested feature is complete. A source implementation, a rendered preview, a packaged build and a test inside iRacing are separate evidence.

## Required progress updates

After **each completed task**, update this same checklist and send the user its refreshed link before moving to the next task. While implementing a task, keep working when new requests arrive; queue them and fold them into this checklist at the next task-completion update. Each update must name the task ID, summarize the change, record the checks performed, identify remaining Windows/iRacing testing or dependencies, and state the next task. Keep implementation, packaged-build verification and user acceptance separate. Reopen a task when the user reports a failure, even when an automated test previously passed. Continue through the agreed work without asking for a separate go-ahead for each routine task.

## Current work order

1. Repair microphone capture and voice recognition; provide a working in-app test.
2. Remove all API-key requirements; implement local “Hey Kerby” activation and an audible engineer response.
3. Audit every offered iRacing track/layout for detection, actual map/live position and coaching/reference coverage; close gaps without claiming incomplete coverage is universal.
4. Refine Settings tabs and checkboxes, smooth tutorial transitions, upgrade the driving dashboard while preserving all measurements, and improve live-input smoothness/latency.
5. Expand complete in-app racecraft lessons with topic-specific photos and annotated visuals.
6. Reorganize lap-history data and redesign its charts.
7. Improve context-aware engineer responses, vocabulary and repetition control.
8. Add recorded-line versus faster-reference animated replay with apexes and synchronized inputs.
9. Add the Garage setup library, local-file/web imports and setup comparison.
10. Add an off-track setup simulator with explicitly labeled predictions and assumptions.
11. Verify changes, build the updated EXE and keep earlier unresolved requirements visible.
12. After every completed task, save this checklist and send the user the updated link.

## 01 — Delivery and updates

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ DEL-01 | Windows PC app delivered as an EXE that installs and launches; user does no coding/building. | **0.14 EXE verified; PC launch pending** | Windows installer built; installs to existing app location |
| ☑ DEL-02 | Put the selected UI, vocabulary and voice assets into the executable that is actually delivered. | **0.14 PACKAGE VERIFIED** | Extracted executable matches the tested UI, coaching code, voice assets and version |
| ☐ DEL-03 | Update the installed app without repeatedly downloading separate full versions. | **PARTIAL** | Verified updater exists; private release-feed access and bootstrap remain unresolved |
| ☐ DEL-04 | Keep lap history, settings and references through an update; preserve previous runtime on interrupted install. | **Source + automated checks** | engineer/updater.py; versioned NSIS install |
| ☑ DEL-05 | Audit every requirement before sending another version and clearly identify remaining gaps. | **CHECKLIST ACTIVE** | 75 original requirements plus the latest feedback and reporting rule recorded; 0.14 package verification remains historical evidence |

## 02 — Selected design and usability

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ UI-01 | Use layout 1, Pit Wall; charcoal and green styling, polished layout and readable typography. | **0.14 package + render checks** | engineer/drive_workspace.py; engineer/theme.py |
| ☐ UI-02 | Put Drive, Analyze, Racecraft, Garage, Engineer, Settings and Help down the left side. | **0.14 package + render checks** | app.py build_ui; independently scrolling rail |
| ☐ UI-03 | Put secondary options down the side too, with compact-window access. | **0.14 package + render checks** | app.py highlight_nav; expandable vertical submenus |
| ☐ UI-04 | Large visible G-force circle on main screen, signed lateral/longitudinal acceleration and resultant. | **Source + automated checks** | engineer/drive_workspace.py |
| ☐ UI-05 | Show an actual map of the current track/layout with live vehicle position. | **PARTIAL COVERAGE** | 417 sourced layouts + observed GPS-route fallback; exact identity required |
| ☐ UI-06 | Main-screen active lap timer, current/last/best times, delta, speed in mph and gear. | **Source + automated checks** | app.py render; engineer/drive_workspace.py |
| ☐ UI-07 | Live telemetry graph includes speed, brake, throttle and steering with reference comparison. | **Source + automated checks** | engineer/position.py; engineer/drive_workspace.py |
| ☐ UI-08 | Clear connected state after valid iRacing telemetry; button changes to iRacing connected. | **Source + automated checks** | engineer/ui_behavior.py connection_state |
| ☐ UI-09 | Show stale/offline states and clear misleading live indicators after data loss. | **Source + automated checks** | SDK age + wall-clock age validation |
| ☐ UI-10 | Mouse wheel works over child controls and navigation; ordinary scrolling stays usable. | **PC TEST NEEDED** | Pointer-aware wheel router exists; physical scroll-wheel test pending |
| ☐ UI-11 | New app name and cooler logo, replacing Apex/Daytona/GR86-only branding. | **Source present** | KerbSignal branding; actual detected car/track; remaining internal legacy paths preserve data |
| ☐ UI-12 | Startup animation with new branding and a preview the user can watch. | **0.14 package + preview verified** | 1.4-second native splash; GIF/MP4 exported from the same painter and saved |
| ☐ UI-13 | Settings tab includes light/dark mode, voice, audio, microphone, overlay, devices and updates. | **Source present** | app.py build_settings_ui |
| ☐ UI-14 | New-user tutorial, reopenable help and explanation of setup/use/reference requirements. | **Source present** | app.py tutorial; returning users stay on Drive |
| ☐ UI-15 | Take inspiration from Trophi.ai feature depth and visual quality. | **PARTIAL** | Feature review exists; current competitor appearance was not verified |
| ☐ UI-16 | Redesign the Settings tabs (General, Voice & audio, Overlay, Devices, Updates) for clear readability and a polished appearance. | **PENDING — 0.14 USER TEST FINDING** | Larger readable labels, generous spacing/padding, stronger text/background contrast and a clearly selected tab. Verify focus/hover states and readability in both light and dark modes. User screenshot shows the current tabs are bland and hard to see; no app fix has been applied yet. |
| ☐ UI-17 | Rework the app checkboxes and boolean controls shown in the first screenshot. | **PENDING — 0.14 USER TEST FINDING** | Replace cramped X-style indicators with clear on/off controls, readable labels, comfortable click targets, consistent alignment and visible focus/disabled states in both themes. Preserve every existing setting and saved preference. This concerns app controls, not the checklist checkmarks. |
| ☐ UI-18 | Make the driving dashboard in the second screenshot more polished and premium while retaining every measurable. | **PENDING — DESIGN REVISION** | Refine typography, spacing, card depth, borders and restrained accent styling within the selected Pit Wall/sidebar design. Keep lap number/current/last/best times, delta, speed/gear, engineer radio, next braking zone, circuit/live position, gaps, G-force, telemetry traces and connection state. |
| ☐ UI-19 | Make live input tracking smoother and more immediate. | **PENDING — PERFORMANCE AND DISPLAY** | Improve steering, pedal, speed, G-force and position refresh consistency; measure capture-to-display latency with valid live SDK data. Preserve raw recorded/coaching inputs, avoid smoothing that adds noticeable lag, and retain clear stale/offline states. The supplied dashboard screenshot shows OFFLINE, so it does not establish live-input latency. |
| ☐ UI-20 | Make transitions between tutorial tabs/steps cleaner and smoother. | **PENDING — 0.14 USER TEST FINDING** | Use short, subtle transitions with stable content spacing, consistent Next/Back controls and a clear current-step indicator. Preserve tutorial progress and keyboard navigation; check for flicker, abrupt layout changes and repeated window opening across pages, themes and supported screen sizes. |

## 03 — Cars, tracks, position and references

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ TEL-01 | Detect the car currently driven; support all iRacing cars instead of Toyota GR86 only. | **Source; PC TEST NEEDED** | engineer/cars.py; SDK identity; car-specific channels can vary |
| ☐ TEL-02 | Detect exact current track and layout automatically; clear old car/track cues after a change. | **Source + automated checks** | SDK metadata; guide/reference profile and condition gates |
| ☐ TEL-03 | Cover all variants of Road Atlanta, Le Mans, Daytona road, Spa, Monza, COTA, full Nürburgring, Tsukuba and Oulton Park. | **PARTIAL COVERAGE** | No verified expert guide/reference for every named variant |
| ☐ TEL-04 | Extend coaching to every iRacing track and variant. | **RECONFIRMED — COMPLETE COVERAGE STILL OPEN** | User reiterates every iRacing track and configuration must be covered for identification, actual map/live position and aligned coaching. Audit per-layout coverage against the official catalogue. Existing 417 maps and observed-route fallback do not verify complete coverage; reference/baseline gaps remain explicit. |
| ☐ TEL-05 | Use actual GPS/position and lap distance rather than elapsed reference lap time for cue location. | **Source + automated checks** | engineer/position.py; engineer/cues.py |
| ☐ TEL-06 | Source the fastest valid lines/laps per car and layout as coaching baselines. | **OUTSTANDING** | No universal licensed fastest-lap catalogue acquired; personal clean laps are not globally optimal |
| ☐ TEL-07 | Allow trustworthy clean-lap/IBT/CSV/provider references; validate car, layout, conditions and provenance. | **Source + automated checks** | engineer/ibt_reference.py; external_reference.py; core.py |
| ☐ TEL-08 | Compare the user racing line to a matching reference and log it for future review. | **Source + automated checks** | GPS line comparison; optimality depends on supplied reference |
| ☐ TEL-09 | Use coaching videos as authored landmark guides when properly aligned to the exact layout. | **PARTIAL** | Guide authoring/alignment exists; no sourced video-guide catalogue for every car/track |

## 04 — Live instructor and explanations

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ COA-01 | Continuous coaching starts when the user drives; appropriate first-run learning dialogue. | **Source + automated checks** | engineer/driving.py; default coaching enabled |
| ☐ COA-02 | Live 3, 2, 1, brake countdowns; hold, release, turn, unwind and throttle phase cues. | **PC TIMING TEST NEEDED** | Cached clips + positional scheduler; acoustic/hardware latency unverified |
| ☐ COA-03 | Correct timing using fresh position/speed; suppress stale, wrong-track, replay, pit and unsafe calls. | **Source + automated checks** | engineer/cues.py; ui_behavior.py |
| ☐ COA-04 | Analyze telemetry immediately and advise braking X meters earlier/later relative to a valid reference. | **Source + automated checks** | engineer/technique.py; bounded single-change experiments |
| ☐ COA-05 | Advise X percentage points more/less brake input where comparison is valid. | **Source + automated checks** | Pedal percentage is not measured brake force |
| ☐ COA-06 | Analyze steering inputs and explain too much/too little wheel angle with matching speed/ratio/line caveats. | **0.14 package + automated checks** | Numerical steering feedback now includes a live mechanism and conditional practice action |
| ☐ COA-07 | Explain WHY during live coaching, not only in the post-session recap. | **0.14 package + automated checks** | Live evidence/action/why added; straight-time speech budget and deferred sentences tested |
| ☐ COA-08 | Use natural lap feedback with a measured finding, useful action and understandable racing concept. | **0.14 package + automated checks** | Conversational measured finding + one bounded action + live explanation |
| ☐ COA-09 | Straights: distance/time to braking, next turn type, car ahead/behind gaps. | **Source + automated checks** | engineer/straight.py; sufficient speech/countdown window required |
| ☐ COA-10 | Report catching the car ahead / car behind gaining by measured amount over a stated interval. | **Source + automated checks** | engineer/situation.py passage-time estimates |
| ☐ COA-11 | Praise good laps and consistency without loops or drowning out instruction. | **Source + automated checks** | engineer/driving.py milestone deduplication/cooldowns |
| ☐ COA-12 | Broader vocabulary: chatty, useful engineer dialogue with Quiet/Standard/Chatty modes. | **REOPENED — vocabulary improvement not accepted** | User still finds the dialogue limited/repetitive. Broaden contextual topics and phrasing; retain critical-call priority. |
| ☐ COA-13 | Safety/spotter/countdowns preempt non-urgent explanations; avoid repetitive, stale or competing speech. | **Source; improvements underway** | Priority dispatch + speech interruption; explanation speech budget being added |
| ☐ COA-14 | Weather, wet conditions, session type and relevant initial situational briefing. | **Source + automated checks** | engineer/situation.py; SDK metadata |
| ☐ COA-15 | Report tire condition and brake/tire warm-up only when data supports it. | **PARTIAL DATA** | iRacing tire data can be pit/delayed snapshots; live brake temperatures unavailable |
| ☐ COA-16 | ABS/TC status and recommendations appropriate to current car and conditions. | **PARTIAL** | Available SDK settings/status; universal validated car-specific adjustment advice outstanding |

## 05 — Voice, microphone and music

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ AUD-01 | Clear English-speaking male engineer voice with a smooth, natural delivery. | **NEW PACK; listening acceptance pending** | Bill/Peter/Michael Pocket TTS; audible samples generated; user must judge naturalness |
| ☑ AUD-02 | Source a free voice pack and verify redistribution licenses. | **LICENSED PACK VERIFIED IN EXE** | Official runtime SHA256 verified; MIT code, CC BY 4 model, CC0/VCTK voice attributions bundled |
| ☐ AUD-03 | Male Australian accent option. | **OUTSTANDING** | No verified free recorded Australian male pack; online style request does not establish recorded identity |
| ☐ AUD-04 | Multiple accent/voice choices and selectable levels of profanity. | **PARTIAL** | American/British choices + Clean/Mild/Unfiltered; phrasing quality being revised |
| ☐ AUD-05 | Voice recognition to speak to engineer, request explanations, recap, car/track and settings. | **REOPENED — user cannot test recognition** | User reports that the microphone is not working in 0.14; recognition remains unverified. Trace selected-device capture through the recognizer. |
| ☐ AUD-06 | Microphone selection, gain, level meter and in-app recognition/hearing test. | **REOPENED — microphone failure reported** | Repair selected input capture and show actual microphone level plus a working in-app recognition test. |
| ☐ AUD-07 | Audio output selection, volume, test voice, mute and timed-cue calibration. | **Source; PC TEST NEEDED** | engineer/audio.py; selected device and cue latency settings |
| ☐ AUD-08 | Engineer opens YouTube for focus music on command. | **Source + automated checks** | engineer/youtube.py; user-directed browser launch |
| ☐ AUD-09 | Explain that legacy/new local voices are synthetic; do not present them as recorded live human speech. | **Recorded limitation** | An entirely recorded free engineer pack with dynamic numbers is not sourced |
| ☐ AUD-10 | Activate the engineer with the phrase “Hey Kerby” and receive a spoken response. | **0.15 WINDOWS TEST BUILD — LIVE DRIVER TEST PENDING** | Native Pocket test speech was decoded by Vosk as hey kirby can you hear me; the wake gate routed the question and Pocket generated the local response. G435 capture delivered 47 blocks at 44.1 kHz. Physical spoken-driver recognition and headset listening still need acceptance. |

## 06 — Race engineering, traffic and pit stops

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ ENG-01 | Detect practice, qualifying and race and adapt priorities/dialogue. | **Source + automated checks** | engineer/pit_engineer.py session_kind; situation.py |
| ☐ ENG-02 | Spotter detects left/right/both and clear; tells driver to hold a predictable line. | **Source; PC TEST NEEDED** | engineer/spotter.py; occupancy does not guarantee a passing lane |
| ☐ ENG-03 | Analyze other cars section pace and identify where the user is faster. | **PARTIAL DATA** | engineer/opponents.py; no opponent pedal/steering telemetry |
| ☐ ENG-04 | Call conditional passing opportunities based on measured pace and space/flag checks. | **Source + automated checks** | engineer/opponents.py; no guaranteed safe overtake instruction |
| ☐ ENG-05 | Detect pit-road entry, actual stationary pit box, service states and pit exit. | **Source; PC TEST NEEDED** | engineer/pit_engineer.py; service requests are not completion evidence |
| ☐ ENG-06 | During pit stop recap race/session pace, position, traffic, measured fuel, tire report and next-lap focus. | **Source; PC TEST NEEDED** | Session-aware pit queue; reported facts only |
| ☐ ENG-07 | Provide car-appropriate setup suggestions after controlled test laps and explain rationale. | **Source; PC TEST NEEDED** | engineer/setup.py; one-change baseline/test workflow |
| ☐ ENG-08 | Keep driver informed about available tire conditions and aggressive/abrupt input patterns. | **Source + automated checks** | TireMonitor + InputStyleMonitor; observations do not establish tire slip/overheating |

## 07 — Overlay and hardware

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ OVR-01 | In-game overlay with small pixel options, placement, opacity and click-through lock. | **PC TEST NEEDED** | engineer/cockpit.py Overlay; 160 × 80 minimum; borderless/windowed iRacing |
| ☐ OVR-02 | Replace overlay car radar with a visible G-force circle. | **Source + bounds checks** | Overlay G circle; traffic remains audible; verify Windows layering |
| ☐ OVR-03 | Recognize wheel base and pedals and show detected devices in settings. | **PARTIAL** | Controller/HID detection + manual roles; cannot automatically read iRacing binding ownership |

## 08 — Learning and review

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ REV-01 | Save race/lap/session times, inputs and racing lines for future review. | **Source + automated checks** | engineer/storage.py; local SQLite history |
| ☐ REV-02 | Accessible post-session recap with performance priorities, inputs, tires and WHY explanations. | **Source + automated checks** | engineer/session_review.py; saved session/pit reports |
| ☐ REV-03 | Racecraft index: drafting, passing/dive-bomb avoidance, weight transfer, red-string analogy and more. | **PARTIAL — expand complete lessons and visuals** | 22 lessons/index entries exist; user requests all learning material inside the app, with relevant photos and diagrams rather than required external reading. |
| ☐ REV-04 | Make lessons actionable through practice experiments and progress comparisons. | **Source; live linkage improving** | Training/Setup/Recap; telemetry-relative experiments |
| ☐ REV-05 | Provide a comprehensive racecraft tool without claiming all unsupported telemetry/reference data exists. | **Ongoing acceptance goal** | Review every checklist row against delivered build and actual iRacing behavior |

## 09 — Verification before next delivery

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☑ QA-01 | Automated regression suite passes after final code changes. | **208 tests pass on Windows / Python 3.14** | Includes duration boundary/rounding checks and real controller rendering of the long gap. Headless tests isolate hardware; native GUI/audio checks are recorded separately. |
| ☑ QA-02 | Render selected layout at multiple sizes in dark/light, connected/offline, with visible G circle. | **Prior revision verified** | 20 production-painter render combinations passed; repeat if changed |
| ☐ QA-03 | Audible voice samples and every cached countdown/spotter clip validated; content/timing reviewed honestly. | **90 CACHED CLIPS CHECKED** | Signal and duration passed; all three new voices have extended samples; user judges naturalness |
| ☑ QA-04 | EXE integrity, embedded source/assets/version and Windows DLL dependencies checked. | **0.14 EXE CHECKED** | NSIS archive integrity, extracted source/model hashes and 89 Windows DLL dependencies checked |
| ☐ QA-05 | Actual Windows launch, live iRacing detection, mic, wheel/pedals, overlay and acoustic cue timing tested. | **MICROPHONE FAILED IN USER TEST** | User cannot test recognition because the microphone fails. Other Windows/iRacing, device, overlay and acoustic-timing acceptance checks remain pending. |

## 10 — Latest 0.14 test feedback

The user requested this checklist before implementation. The following feature changes are pending; updating the checklist does not complete the app fixes.

### Microphone and recognition

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ MIC-FIX-01 | Fix microphone detection and audio capture. | **WINDOWS CAPTURE / GENERATED-ASR VERIFIED; DRIVER TEST PENDING** | The 0.15 test package bundles pinned Vosk and Pocket assets. Generated test phrases decoded correctly; the G435 default microphone delivered 47 PCM blocks at 44.1 kHz, with no live audio saved. First-use conversion initializes before capture. Selected live speech, listening and simulator acceptance remain open. |
| ☐ MIC-FIX-02 | Connect the selected microphone to the voice recognizer correctly. | **WINDOWS CAPTURE / GENERATED-ASR VERIFIED; DRIVER TEST PENDING** | The 0.15 test package bundles pinned Vosk and Pocket assets. Generated test phrases decoded correctly; the G435 default microphone delivered 47 PCM blocks at 44.1 kHz, with no live audio saved. First-use conversion initializes before capture. Selected live speech, listening and simulator acceptance remain open. |
| ☐ MIC-FIX-03 | Provide a working in-app test with an input meter and live recognized-text display. | **WINDOWS CAPTURE / GENERATED-ASR VERIFIED; DRIVER TEST PENDING** | The 0.15 test package bundles pinned Vosk and Pocket assets. Generated test phrases decoded correctly; the G435 default microphone delivered 47 PCM blocks at 44.1 kHz, with no live audio saved. First-use conversion initializes before capture. Selected live speech, listening and simulator acceptance remain open. |

### Completely key-free AI

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☑ KEY-01 | Remove the API-key field shown in the user screenshot. | **PACKAGED IN 0.15 TEST BUILD** | The local-chat screen has no API-key field or cloud sign-in. The packaged source and native UI startup were verified. |
| ☐ KEY-02 | Replace the key-dependent live-engineer connection/talking workflow. | **0.15 SOURCE IMPLEMENTED — NOT RELEASED** | Key-based UI removed; local racing answers, follow-up memory, Hey Kerby gate and optional free offline model chat added. 203 tests pass; Linux CPU inference verified. Windows microphone/audio response and packaged 0.15 remain untested. |
| ☐ KEY-03 | Make AI coaching, conversation, speech and recognition work without API keys. | **0.15 SOURCE IMPLEMENTED — NOT RELEASED** | Key-based UI removed; local racing answers, follow-up memory, Hey Kerby gate and optional free offline model chat added. 203 tests pass; Linux CPU inference verified. Windows microphone/audio response and packaged 0.15 remain untested. |

### Complete visual racecraft lessons

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ LEARN-01 | Include complete lessons in the app without requiring external reading. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ LEARN-02 | Explain how each technique works, why it helps, common mistakes and practice exercises. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ LEARN-03 | Add relevant racing photos and annotated instructional diagrams for every topic. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ LEARN-04 | Keep lesson text and visuals available inside the app. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |

### Lap history and charts

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ HIST-01 | Organize date/time, session, track/layout, car, lap number and lap time into readable columns. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ HIST-02 | Group individual laps clearly under their sessions. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ HIST-03 | Redesign charts with readable axes, units, legends and meaningful comparisons. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ HIST-04 | Make best laps, improvements and slower sections easy to identify. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |

### Smarter engineer and vocabulary

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ SMART-01 | Use the current car, track, session, telemetry and driver question to choose a relevant response. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ SMART-02 | Expand topic-specific dialogue and natural phrasing. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ SMART-03 | Remember recent calls and reduce repetitive commentary. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ SMART-04 | Give useful corrections with why explanations while protecting critical driving calls. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |

### Driving-line analysis and replay

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ REPLAY-01 | Display the recorded driving line for each selected lap. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ REPLAY-02 | Highlight corner apexes on the map. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ REPLAY-03 | Animate two small car models: the recorded lap and a genuinely faster reference. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ REPLAY-04 | Match reference laps to the same car and track layout. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ REPLAY-05 | Synchronize steering/wheel inputs and brake/throttle traces with playback. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ REPLAY-06 | Provide playback controls for inspecting where the laps differ. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |

### Garage setup library

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ SETS-01 | Add a dedicated Setups tab in Garage. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ SETS-02 | Save and organize named setups for each car. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ SETS-03 | Import setups through the file picker and supported web downloads. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ SETS-04 | Show supported setup information and differences between saved versions. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |

### Off-track setup simulator

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ SIM-01 | Add a simulator/comparison tab for the current and proposed setups without a track session. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ SIM-02 | Explain predicted handling and estimated performance changes. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ SIM-03 | Show assumptions and confidence; validate claimed speed gains against measured lap data when available. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |

### Verification and delivery of this revision

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☑ DEL-NEXT-01 | Add every latest request to the existing master checklist. | **CHECKLIST UPDATED** | All 34 latest acceptance checks added; app changes remain pending. |
| ☐ DEL-NEXT-02 | Verify implemented workflows and identify remaining Windows/iRacing acceptance testing. | **PENDING** | Not implemented in the delivered 0.14 build; track implementation, packaging and acceptance separately. |
| ☐ DEL-NEXT-03 | Package the completed changes into the downloadable app. | **0.15 TEST BUILD — PARTIAL BACKLOG DELIVERY** | New x64 EXE includes free local chat, microphone/recognition work and UI-24; earlier unresolved checklist items remain open. Isolated installer extraction and native app checks are recorded separately from iRacing acceptance. |

### Reporting workflow

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☑ WF-01 | Send an updated version of this same checklist after every completed task. | **RECORDED AND ACTIVE** | Each completion update must include the task ID, change, validation, outstanding testing and next task. |
| ☑ WF-02 | Keep working on the current task when new requests arrive; queue those requests and add them at the next completed-task checklist update. | **RECORDED AND ACTIVE** | Requested by the user while inspecting 0.14. Task-completion updates continue without pausing implementation for each new message. |

An off-track model can estimate performance. Proving that a setup is faster requires measured lap data; the simulator must label predictions, assumptions and confidence.


## 11 — Additional inspection requests and free local chat

| Check | Request | Current state | Evidence / remaining work |
|---|---|---|---|
| ☐ COA-17 | First-driving-lap car briefing | **PENDING** | Identify the exact SDK car model/generation on the first driven lap of a new session or after a car change. Speak once, in a clear window, with one verified relevant characteristic and a useful driving implication. Use a sourced exact-car fact catalogue; never infer traits from brand alone. Unknown cars get identity only. Do not treat a mid-session connection as race lap one or repeat on pit exit. |
| ☐ COA-18 | Measured live time-gain feedback | **PENDING** | Compare aligned, clean, compatible reference sections and announce meaningful positive improvements with the measured seconds and reference named. Respect conditions/traffic/freshness and minimum thresholds. Do not call raw acceleration or a changing global delta a proven technique improvement. Deduplicate and protect driving/spotter calls. |
| ☐ COA-19 | Strong corner-exit recognition and varied praise | **PENDING** | Detect a sustained better exit from measured matched exit speed, section/straight time or independently measured relative gain. Explain the observed improvement; causation is qualified. Rotate unique concise phrases with memory/cooldowns and distinguish own-reference gains from catching another car. Prevent praise loops and suppression of useful corrections. |
| ☐ UI-21 | Sidebar icons | **PENDING** | Consistent recognizable icons for Drive, Analyze, Racecraft, Garage, Engineer, Settings and Help. Preserve readable text, selected/focus/hover states, left-side navigation, both themes, compact displays and DPI scaling. |
| ☐ OVR-04 | Overlay support across display formats | **PENDING** | Retain all-format target: windowed, borderless, exclusive fullscreen and VR; include single/triple monitors, ultrawide, common resolutions and DPI scales. Separate rendering integration as needed, with explicit detected mode, working calibration and compatibility matrix. Do not claim support based on removing the existing warning; require per-mode Windows/headset testing. Preserve compact G-force overlay. |
| ☐ UI-22 | Redesign Engineer radio and live details | **PENDING** | Replace dense ungrouped text with readable connection/telemetry health, current instruction and reason, input/reference comparison, equipment/tire caveats, opponent insights and compact timestamped radio timeline. Preserve every useful measurement, show human-readable stale age, limit alert noise, consistent controls, no cramped checkboxes or heavy white borders. |
| ☐ UI-23 | Actual track-turn labels and current-turn identification | **PENDING** | Replace generic Braking zone N labels in the corner list with verified actual circuit/layout turn numbers and names, e.g. Turn 4 — [official name]. Match markers to the exact track configuration, including combined/chicane turn ranges; never equate detection order or braking-zone numbering with official turn numbering. Highlight the current turn from fresh validated lap-distance/GPS position in live views. Keep saved-lap analysis labels tied to that lap's profile, distinguish manual selected row from current live turn, clear stale/wrong-layout highlighting, and show Unmapped corner where turn identity is not verified. Queued only; no source edit, test or saved checklist update. |
| ☑ UI-24 | Elapsed-duration formatting switches to minutes after 60 seconds | **PACKAGED FIX — 208 WINDOWS TESTS PASS** | Gaps, next-brake ETA, recap/setup lap times and observation timestamps use minutes at 60 seconds: 153.7s → 2:33.7. Rounding carries correctly; millisecond lap precision remains. Signed gains/deltas remain seconds. Source matched the final extracted test build. Fresh install, repair and native Tk launch checks passed. |
| — CODEX-01 | Settings OAuth connection | **SUPERSEDED BY USER** | User requires zero ChatGPT/Codex allowance use and zero API charges. Do not implement hosted subscription inference. A local model is a separate assistant and does not inherit this chat. |
| — CODEX-02 | Embedded subscription Codex session | **SUPERSEDED BY USER** | User requires zero ChatGPT/Codex allowance use and zero API charges. Do not implement hosted subscription inference. A local model is a separate assistant and does not inherit this chat. |
| — CODEX-03 | Subscription entitlement / usage | **SUPERSEDED BY USER** | User requires zero ChatGPT/Codex allowance use and zero API charges. Do not implement hosted subscription inference. A local model is a separate assistant and does not inherit this chat. |
| — CODEX-04 | Subscription Codex microphone / voice | **SUPERSEDED BY USER** | User requires zero ChatGPT/Codex allowance use and zero API charges. Do not implement hosted subscription inference. A local model is a separate assistant and does not inherit this chat. |
| ☐ FREE-01 | No account, API charges or ChatGPT/Codex allowance for chat | **0.15 SOURCE IMPLEMENTED — NOT RELEASED** | LocalAI, LocalEngineer and app UI; 203 regression tests pass. Actual Qwen3 0.6B Linux CPU inference completed in 9.93 s including startup. Small-model answer quality remains limited; Windows/device tests pending. One-time model/runtime download about 632 MiB, then inference stays on this PC. No coding-agent tools; extended chat pauses while driving. |
| ☐ FREE-02 | Local chat with typed questions, racing context and optional speech | **0.15 SOURCE IMPLEMENTED — NOT RELEASED** | LocalAI, LocalEngineer and app UI; 203 regression tests pass. Actual Qwen3 0.6B Linux CPU inference completed in 9.93 s including startup. Small-model answer quality remains limited; Windows/device tests pending. One-time model/runtime download about 632 MiB, then inference stays on this PC. No coding-agent tools; extended chat pauses while driving. |
| ☐ FREE-03 | In-app free-model installation, cancellation and offline inference | **0.15 SOURCE IMPLEMENTED — NOT RELEASED** | LocalAI, LocalEngineer and app UI; 203 regression tests pass. Actual Qwen3 0.6B Linux CPU inference completed in 9.93 s including startup. Small-model answer quality remains limited; Windows/device tests pending. One-time model/runtime download about 632 MiB, then inference stays on this PC. No coding-agent tools; extended chat pauses while driving. |
| ☑ GH-01 | Supply all project source for colleague / GitHub upload. | **HANDOFF ARCHIVE VERIFIED** | GitHub-ready source, tests, build scripts, all current requirements, asset manifests/restoration scripts, previews, licences, checksums and handoff notes included. Runtime EXE and large downloaded models are separate release assets. Source also uploaded to Kdyanamicstudios/Kerbsignal-2 at the user’s request. |
| ☑ GH-02 | Upload this Windows version to a separate GitHub repository. | **SOURCE UPLOADED AND VERIFIED** | [Kdyanamicstudios/Kerbsignal-2](https://github.com/Kdyanamicstudios/Kerbsignal-2) contains the complete Windows/Python source, maps, voice clips, build tooling, checklist and validation records. Installer/runtime binaries remain separate distribution assets. The existing repository was not modified. |

## Update log

- October 31, 2026: GH-02 delivery checkpoint: uploaded this Windows/Python snapshot to the user-selected new repository, https://github.com/Kdyanamicstudios/Kerbsignal-2. All 1,520 source files were checked against their local Git object fingerprints. Runtime/model binaries and the installer remain outside repository source. The original repository and its Rust/Assetto Corsa work were not modified.

- October 31, 2026: Final delivery validation passed for the single x64 0.15 EXE: 6,968 extracted files matched, repeated installation repaired into a fresh runtime and retained earlier versions, and the extracted application passed native Tk checks. Generated Hey Kerby speech decoded correctly at 16, 44.1 and 48 kHz on Windows. The test installer, synchronized checklist and refreshed GitHub source ZIP are saved together. Actual driver speech/listening and iRacing testing remain open. Next tasks are the coverage/UI backlog after test-build acceptance.

- October 31, 2026: Windows delivery checkpoint: native x64 test installer built and first isolated extraction passed. 208 checks pass with the packaged Python; real Tk startup and all 15 pages render. Pocket speech, Vosk decoding, wake routing and local response generation pass; G435 capture delivered 47 blocks. UI-24 and API-key-field removal are included. Live driver speech/listening/iRacing and other backlog rows remain pending. Final x64 installer validation passed: 6,968 extracted files matched SHA256, repair created a fresh runtime and preserved the previous version, launcher checks passed, and extracted native Tk rendered all 15 pages. No existing user installation or public release was changed.

- October 31, 2026: UI-24 source milestone complete; 208 Windows tests pass. Corrected long gaps and next-brake ETA plus lap/elapsed times in recap and setup views; retained signed differences. Native hidden Tk startup/rendering of all 15 pages passed. Pinned Pocket speech generated both test phrases and Vosk recognized them on Windows. The G435 default microphone delivered PCM blocks at 44.1 kHz; live audio was discarded. First-use conversion is now loaded before opening capture to avoid dropping initial words. Actual spoken-driver recognition, listening quality, simulator timing and release extraction remain next. User confirmed fully local/free, with no Codex sign-in.

- October 31, 2026: Continued in this chat from the recovered 0.15 source. DEL-NEXT-02 regression checkpoint: all 203 tests pass on Windows/Python 3.14. The previous failures were incomplete Windows mocks in headless tests, followed by open test databases after aborted construction; they did not establish a production microphone failure. Test isolation fixed without bypassing the coaching assertions. Native GUI, recognition dependencies, physical microphone and packaging remain next.

- October 31, 2026: Free local chat and Hey Kerby source milestone; 203 tests pass and real Linux CPU model response recorded. KEY-01–03 and AUD-10 source implemented; Windows/package acceptance pending. Added all requests queued during the outage, including exact turn labels and minute formatting. Subscription OAuth request superseded by zero-allowance requirement. GH-01 handoff packaged; next work remains coverage/UI and the listed pending requirements.

- October 30, 2026: Microphone/recognition implementation milestone saved for working version 0.15. MIC-FIX-01–03 now have implemented source and automated/recorded-audio evidence; packaged/physical Windows acceptance remains pending. Added WF-02 to keep working and collect incoming tasks until each completion update. Next: remove key-dependent engineer controls and add the local wake-response workflow.

- October 30, 2026: Added UI-20 for cleaner, smoother tutorial-tab/step transitions. App implementation remains pending.

- October 30, 2026: Reaffirmed complete track/layout coverage in TEL-04; added UI-17 app checkbox redesign, UI-18 premium dashboard retaining all metrics, UI-19 smoother low-latency input displays, and AUD-10 local “Hey Kerby” activation with a spoken response. All four new app changes remain pending.

- October 30, 2026: Added UI-16 from the 0.14 Settings screenshot: tab appearance/readability redesign. Status pending; this update records the finding and does not claim the app is fixed.

- October 30, 2026: Added 34 checks from the latest user feedback and the completion-reporting rule. Reopened microphone/recognition, vocabulary and racecraft completeness after the user report. The latest app fixes have not started.

## Completion rule

This checklist contains **134 tracked requirements**, including four superseded subscription items. Check a box only when the requested result is included in the delivered artifact and its stated validation has actually occurred. Keep partial coverage and unavailable telemetry explicit. Re-read this checklist before each release; update the same file instead of starting a disconnected to-do list.

Immediate live-coach examples must include actual measured values when available; otherwise omit the numbers. “You braked 12 metres earlier than your reference; try moving the marker 10 metres later. The aim is to preserve entry speed while leaving room for a smooth brake release.” This is illustrative wording, not evidence from the user’s session.
