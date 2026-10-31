from pathlib import Path
sections={
'01 — Delivery and updates':[
('DEL-01','Windows PC app delivered as an EXE that installs and launches; user does no coding/building.','0.14 EXE verified; PC launch pending','Windows installer built; installs to existing app location'),
('DEL-02','Put the selected UI, vocabulary and voice assets into the executable that is actually delivered.','0.14 PACKAGE VERIFIED','Extracted executable matches the tested UI, coaching code, voice assets and version'),
('DEL-03','Update the installed app without repeatedly downloading separate full versions.','PARTIAL','Verified updater exists; private release-feed access and bootstrap remain unresolved'),
('DEL-04','Keep lap history, settings and references through an update; preserve previous runtime on interrupted install.','Source + automated checks','engineer/updater.py; versioned NSIS install'),
('DEL-05','Audit every requirement before sending another version and clearly identify remaining gaps.','CHECKLIST ACTIVE','75 requirements recorded; source/tests, assets and extracted-package verification completed'),
],
'02 — Selected design and usability':[
('UI-01','Use layout 1, Pit Wall; charcoal and green styling, polished layout and readable typography.','0.14 package + render checks','engineer/drive_workspace.py; engineer/theme.py'),
('UI-02','Put Drive, Analyze, Racecraft, Garage, Engineer, Settings and Help down the left side.','0.14 package + render checks','app.py build_ui; independently scrolling rail'),
('UI-03','Put secondary options down the side too, with compact-window access.','0.14 package + render checks','app.py highlight_nav; expandable vertical submenus'),
('UI-04','Large visible G-force circle on main screen, signed lateral/longitudinal acceleration and resultant.','Source + automated checks','engineer/drive_workspace.py'),
('UI-05','Show an actual map of the current track/layout with live vehicle position.','PARTIAL COVERAGE','417 sourced layouts + observed GPS-route fallback; exact identity required'),
('UI-06','Main-screen active lap timer, current/last/best times, delta, speed in mph and gear.','Source + automated checks','app.py render; engineer/drive_workspace.py'),
('UI-07','Live telemetry graph includes speed, brake, throttle and steering with reference comparison.','Source + automated checks','engineer/position.py; engineer/drive_workspace.py'),
('UI-08','Clear connected state after valid iRacing telemetry; button changes to iRacing connected.','Source + automated checks','engineer/ui_behavior.py connection_state'),
('UI-09','Show stale/offline states and clear misleading live indicators after data loss.','Source + automated checks','SDK age + wall-clock age validation'),
('UI-10','Mouse wheel works over child controls and navigation; ordinary scrolling stays usable.','PC TEST NEEDED','Pointer-aware wheel router exists; physical scroll-wheel test pending'),
('UI-11','New app name and cooler logo, replacing Apex/Daytona/GR86-only branding.','Source present','KerbSignal branding; actual detected car/track; remaining internal legacy paths preserve data'),
('UI-12','Startup animation with new branding and a preview the user can watch.','0.14 package + preview verified','1.4-second native splash; GIF/MP4 exported from the same painter and saved'),
('UI-13','Settings tab includes light/dark mode, voice, audio, microphone, overlay, devices and updates.','Source present','app.py build_settings_ui'),
('UI-14','New-user tutorial, reopenable help and explanation of setup/use/reference requirements.','Source present','app.py tutorial; returning users stay on Drive'),
('UI-15','Take inspiration from Trophi.ai feature depth and visual quality.','PARTIAL','Feature review exists; current competitor appearance was not verified'),
],
'03 — Cars, tracks, position and references':[
('TEL-01','Detect the car currently driven; support all iRacing cars instead of Toyota GR86 only.','Source; PC TEST NEEDED','engineer/cars.py; SDK identity; car-specific channels can vary'),
('TEL-02','Detect exact current track and layout automatically; clear old car/track cues after a change.','Source + automated checks','SDK metadata; guide/reference profile and condition gates'),
('TEL-03','Cover all variants of Road Atlanta, Le Mans, Daytona road, Spa, Monza, COTA, full Nürburgring, Tsukuba and Oulton Park.','PARTIAL COVERAGE','No verified expert guide/reference for every named variant'),
('TEL-04','Extend coaching to every iRacing track and variant.','PARTIAL','Generic telemetry coach/learning works; complete licensed reference coverage remains outstanding'),
('TEL-05','Use actual GPS/position and lap distance rather than elapsed reference lap time for cue location.','Source + automated checks','engineer/position.py; engineer/cues.py'),
('TEL-06','Source the fastest valid lines/laps per car and layout as coaching baselines.','OUTSTANDING','No universal licensed fastest-lap catalogue acquired; personal clean laps are not globally optimal'),
('TEL-07','Allow trustworthy clean-lap/IBT/CSV/provider references; validate car, layout, conditions and provenance.','Source + automated checks','engineer/ibt_reference.py; external_reference.py; core.py'),
('TEL-08','Compare the user racing line to a matching reference and log it for future review.','Source + automated checks','GPS line comparison; optimality depends on supplied reference'),
('TEL-09','Use coaching videos as authored landmark guides when properly aligned to the exact layout.','PARTIAL','Guide authoring/alignment exists; no sourced video-guide catalogue for every car/track'),
],
'04 — Live instructor and explanations':[
('COA-01','Continuous coaching starts when the user drives; appropriate first-run learning dialogue.','Source + automated checks','engineer/driving.py; default coaching enabled'),
('COA-02','Live 3, 2, 1, brake countdowns; hold, release, turn, unwind and throttle phase cues.','PC TIMING TEST NEEDED','Cached clips + positional scheduler; acoustic/hardware latency unverified'),
('COA-03','Correct timing using fresh position/speed; suppress stale, wrong-track, replay, pit and unsafe calls.','Source + automated checks','engineer/cues.py; ui_behavior.py'),
('COA-04','Analyze telemetry immediately and advise braking X meters earlier/later relative to a valid reference.','Source + automated checks','engineer/technique.py; bounded single-change experiments'),
('COA-05','Advise X percentage points more/less brake input where comparison is valid.','Source + automated checks','Pedal percentage is not measured brake force'),
('COA-06','Analyze steering inputs and explain too much/too little wheel angle with matching speed/ratio/line caveats.','0.14 package + automated checks','Numerical steering feedback now includes a live mechanism and conditional practice action'),
('COA-07','Explain WHY during live coaching, not only in the post-session recap.','0.14 package + automated checks','Live evidence/action/why added; straight-time speech budget and deferred sentences tested'),
('COA-08','Use natural lap feedback with a measured finding, useful action and understandable racing concept.','0.14 package + automated checks','Conversational measured finding + one bounded action + live explanation'),
('COA-09','Straights: distance/time to braking, next turn type, car ahead/behind gaps.','Source + automated checks','engineer/straight.py; sufficient speech/countdown window required'),
('COA-10','Report catching the car ahead / car behind gaining by measured amount over a stated interval.','Source + automated checks','engineer/situation.py passage-time estimates'),
('COA-11','Praise good laps and consistency without loops or drowning out instruction.','Source + automated checks','engineer/driving.py milestone deduplication/cooldowns'),
('COA-12','Broader vocabulary: chatty, useful engineer dialogue with Quiet/Standard/Chatty modes.','0.14 package + automated checks','32 input-event phrases, eight straight openings, eight gap openings, varied reference feedback; existing pit vocabulary retained'),
('COA-13','Safety/spotter/countdowns preempt non-urgent explanations; avoid repetitive, stale or competing speech.','Source; improvements underway','Priority dispatch + speech interruption; explanation speech budget being added'),
('COA-14','Weather, wet conditions, session type and relevant initial situational briefing.','Source + automated checks','engineer/situation.py; SDK metadata'),
('COA-15','Report tire condition and brake/tire warm-up only when data supports it.','PARTIAL DATA','iRacing tire data can be pit/delayed snapshots; live brake temperatures unavailable'),
('COA-16','ABS/TC status and recommendations appropriate to current car and conditions.','PARTIAL','Available SDK settings/status; universal validated car-specific adjustment advice outstanding'),
],
'05 — Voice, microphone and music':[
('AUD-01','Clear English-speaking male engineer voice with a smooth, natural delivery.','NEW PACK; listening acceptance pending','Bill/Peter/Michael Pocket TTS; audible samples generated; user must judge naturalness'),
('AUD-02','Source a free voice pack and verify redistribution licenses.','LICENSED PACK VERIFIED IN EXE','Official runtime SHA256 verified; MIT code, CC BY 4 model, CC0/VCTK voice attributions bundled'),
('AUD-03','Male Australian accent option.','OUTSTANDING','No verified free recorded Australian male pack; online style request does not establish recorded identity'),
('AUD-04','Multiple accent/voice choices and selectable levels of profanity.','PARTIAL','American/British choices + Clean/Mild/Unfiltered; phrasing quality being revised'),
('AUD-05','Voice recognition to speak to engineer, request explanations, recap, car/track and settings.','PC TEST NEEDED','Windows local command grammar; optional online conversation'),
('AUD-06','Microphone selection, gain, level meter and in-app recognition/hearing test.','Source; PC TEST NEEDED','engineer/microphone.py; Settings voice/audio'),
('AUD-07','Audio output selection, volume, test voice, mute and timed-cue calibration.','Source; PC TEST NEEDED','engineer/audio.py; selected device and cue latency settings'),
('AUD-08','Engineer opens YouTube for focus music on command.','Source + automated checks','engineer/youtube.py; user-directed browser launch'),
('AUD-09','Explain that legacy/new local voices are synthetic; do not present them as recorded live human speech.','Recorded limitation','An entirely recorded free engineer pack with dynamic numbers is not sourced'),
],
'06 — Race engineering, traffic and pit stops':[
('ENG-01','Detect practice, qualifying and race and adapt priorities/dialogue.','Source + automated checks','engineer/pit_engineer.py session_kind; situation.py'),
('ENG-02','Spotter detects left/right/both and clear; tells driver to hold a predictable line.','Source; PC TEST NEEDED','engineer/spotter.py; occupancy does not guarantee a passing lane'),
('ENG-03','Analyze other cars section pace and identify where the user is faster.','PARTIAL DATA','engineer/opponents.py; no opponent pedal/steering telemetry'),
('ENG-04','Call conditional passing opportunities based on measured pace and space/flag checks.','Source + automated checks','engineer/opponents.py; no guaranteed safe overtake instruction'),
('ENG-05','Detect pit-road entry, actual stationary pit box, service states and pit exit.','Source; PC TEST NEEDED','engineer/pit_engineer.py; service requests are not completion evidence'),
('ENG-06','During pit stop recap race/session pace, position, traffic, measured fuel, tire report and next-lap focus.','Source; PC TEST NEEDED','Session-aware pit queue; reported facts only'),
('ENG-07','Provide car-appropriate setup suggestions after controlled test laps and explain rationale.','Source; PC TEST NEEDED','engineer/setup.py; one-change baseline/test workflow'),
('ENG-08','Keep driver informed about available tire conditions and aggressive/abrupt input patterns.','Source + automated checks','TireMonitor + InputStyleMonitor; observations do not establish tire slip/overheating'),
],
'07 — Overlay and hardware':[
('OVR-01','In-game overlay with small pixel options, placement, opacity and click-through lock.','PC TEST NEEDED','engineer/cockpit.py Overlay; 160 × 80 minimum; borderless/windowed iRacing'),
('OVR-02','Replace overlay car radar with a visible G-force circle.','Source + bounds checks','Overlay G circle; traffic remains audible; verify Windows layering'),
('OVR-03','Recognize wheel base and pedals and show detected devices in settings.','PARTIAL','Controller/HID detection + manual roles; cannot automatically read iRacing binding ownership'),
],
'08 — Learning and review':[
('REV-01','Save race/lap/session times, inputs and racing lines for future review.','Source + automated checks','engineer/storage.py; local SQLite history'),
('REV-02','Accessible post-session recap with performance priorities, inputs, tires and WHY explanations.','Source + automated checks','engineer/session_review.py; saved session/pit reports'),
('REV-03','Racecraft index: drafting, passing/dive-bomb avoidance, weight transfer, red-string analogy and more.','Source present','22 searchable original lessons with exercises and sources'),
('REV-04','Make lessons actionable through practice experiments and progress comparisons.','Source; live linkage improving','Training/Setup/Recap; telemetry-relative experiments'),
('REV-05','Provide a comprehensive racecraft tool without claiming all unsupported telemetry/reference data exists.','Ongoing acceptance goal','Review every checklist row against delivered build and actual iRacing behavior'),
],
'09 — Verification before next delivery':[
('QA-01','Automated regression suite passes after final code changes.','182 tests passed','Full suite passed after live-explanation/voice/UI changes; includes six new explanation-window tests'),
('QA-02','Render selected layout at multiple sizes in dark/light, connected/offline, with visible G circle.','Prior revision verified','20 production-painter render combinations passed; repeat if changed'),
('QA-03','Audible voice samples and every cached countdown/spotter clip validated; content/timing reviewed honestly.','90 CACHED CLIPS CHECKED','Signal and duration passed; all three new voices have extended samples; user judges naturalness'),
('QA-04','EXE integrity, embedded source/assets/version and Windows DLL dependencies checked.','0.14 EXE CHECKED','NSIS archive integrity, extracted source/model hashes and 89 Windows DLL dependencies checked'),
('QA-05','Actual Windows launch, live iRacing detection, mic, wheel/pedals, overlay and acoustic cue timing tested.','USER-PC TEST NEEDED','Cannot complete native Windows/iRacing hardware tests in this environment'),
]}
lines=['# KerbSignal — master requirements checklist','', 'Owner: Rakiem Eddy. Canonical selection: **Pit Wall, option 1, with navigation down the left side.**','', 'Updated: October 30, 2026. This is the working checklist for the app, not a claim that every requested feature is complete. A source implementation, a rendered preview, a packaged build and a test inside iRacing are separate evidence.','', '## Current work order','', '1. Verify the integrated live evidence/action/WHY delivery and expanded vocabulary.','2. Review the new licensed Pocket TTS voice samples and test delivery in Windows.','3. Test the delivered 0.14 EXE in Windows/iRacing, including physical audio timing.','4. Use this checklist to track any failed acceptance check and the unresolved coverage/data gaps.','5. Keep this same checklist current for every following build.','']
count=0
for title,rows in sections.items():
 lines+=['## '+title,'','| Check | Request | Current state | Evidence / remaining work |','|---|---|---|---|']
 for id,req,status,evidence in rows:
  count+=1;lines.append(f'| {"☑" if id in {"DEL-02","DEL-05","AUD-02","REV-03","QA-01","QA-02","QA-04"} else "☐"} {id} | {req} | **{status}** | {evidence} |')
 lines.append('')
lines+=['## Completion rule','',f'This checklist contains **{count} tracked requirements**. Check a box only when the requested result is included in the delivered artifact and its stated validation has actually occurred. Keep partial coverage and unavailable telemetry explicit. Re-read this checklist before each release; update the same file instead of starting a disconnected to-do list.','', 'Immediate live-coach examples must include actual measured values when available; otherwise omit the numbers. “You braked 12 metres earlier than your reference; try moving the marker 10 metres later. The aim is to preserve entry speed while leaving room for a smooth brake release.” This is illustrative wording, not evidence from the user’s session.','']
text='\n'.join(lines)
Path('KerbSignal_Master_Checklist.md').write_text(text)
Path('race_engineer/MASTER_CHECKLIST.md').write_text(text)
Path('AGENTS.md').write_text('# KerbSignal project workflow\n\nRead race_engineer/MASTER_CHECKLIST.md before changes and every release. It is the canonical list of the user’s requests. Keep it and KerbSignal_Master_Checklist.md synchronized. Preserve the selected Pit Wall design with primary and secondary navigation down the left side. Update the same checklist after work; record source, packaged-build and actual Windows/iRacing validation separately. Do not claim preview/source work is already in the installer. Never describe personal reference laps as universal optimal/world-record laps or unavailable tire/opponent channels as measured. The user expects all building/coding done here.\n')
print('Created master checklist:',count,'requirements')
