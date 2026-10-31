# KerbSignal 0.12 — feature review

The Trophi.ai feature review informed priorities; KerbSignal uses original code and learning content. It does not copy proprietary voices, laps, scoring or interface assets.

| Published capability | KerbSignal implementation | Practical limit |
|---|---|---|
| Immediate skill feedback | Live distance-aligned brake target and steering-wheel comparison | Requires a comparable reference; no inferred tire-slip diagnosis |
| Corner analysis | Time-loss ranking, braking marker and peak-input corrections, throttle pickup and steering comparison | Reference-relative observations, not proof of cause |
| Focused training | Technique filters in Training, plus 22 searchable racecraft lessons with practice exercises | Filters organize feedback; no trained 0–100 score or completion certification |
| Reference telemetry | Live speed and pedal traces with dashed reference overlays; steering trace | No synchronized expert video replay |
| Contextual voice | Brief conversational corner reviews, prioritized traffic and positioned calls; optional online conversation | Free speech is local neural synthesis, not a recorded human engineer |
| Lap review | Persistent lap history, recorded line, clean-reference import, setup baseline/test runs | A personal best is not a globally optimal lap |

Primary feature descriptions reviewed October 30, 2026:
- https://www.trophi.ai/sim-racing/real-time-skill-analysis/
- https://www.trophi.ai/sim-racing-features/lap-analysis
- https://www.trophi.ai/sim-racing-features/live-telemetry-overlays

## Earlier requirements carried forward

Automatic car/layout identity, mph display, lap timers, telemetry logging, voice commands, free American/British neural voices, style settings, optional Australian-accent online voice, YouTube launch, left/right traffic calls, configurable compact G-circle overlay, hardware detection, settings, tutorial, and setup tests remain in the application.

Positioned coaching still requires a matched clean reference or authored guide. The application cannot provide verified expert braking markers on the first lap of every car/layout. This release bundles 417 source-layout maps matched by exact internal track name; coverage of the current iRacing catalogue is not guaranteed. Unmatched layouts use observed GPS routes. GPX-based map positions are approximations; live SDK GPS is preferred. Map geometry is not an optimal racing line.

Still outstanding: a licensed comprehensive expert-lap library, recorded Australian engineer voice pack, hosted automatic-update channel, and real Windows/iRacing end-to-end testing. The verified/resumable updater has an owner-private release host; anonymous downloads await explicit public-read authorization. The standalone installer updates the existing install and retains its history/settings directory.

## Interpretation of numerical feedback

Brake percentage is simulator pedal input. A change from 60% to 68% is eight percentage points, not eight percent more physical pressure. Suggested steps are capped at eight percentage points, 15 meters later or 20 meters earlier, and withheld when approach speeds differ by more than 10%. These are practice experiments against a matched reference, not guarantees that later braking is faster.

Steering comparisons use absolute steering-wheel angle in degrees at comparable distance and speed. They require the same steering ratio/calibration and an appropriate line. More or less wheel angle is not automatically understeer or oversteer. The UI explicitly preserves that distinction.

## Microphone test

Settings → Voice & audio: choose a microphone, set gain, then Start microphone test. Say “Engineer microphone check.” Watch the input meter and recognized text/confidence. Test mode does not execute driving commands. Stop the test before enabling normal commands. Save voice & audio stores microphone selection/gain. Selected input also applies to optional online conversation. Local command recognition requires a Windows English speech-recognition language pack. Local test audio is neither saved nor uploaded; optional online voice is a separate opt-in service.

## Validation scope

Automated tests cover controller flow, reference matching, coaching priorities, numerical correction direction and limits, steering comparison, microphone command isolation, map identity and existing app behavior. Runtime dependency and installer checks are performed separately. Native rendering, hardware recognition, acoustic latency, microphone streaming and live iRacing operation still require Windows validation.

## Session understanding and opponent scouting

Session recaps are accessible from Analyze, including after restarting the app. Select a session in Lap history and open its recap. Stopping a recording also prepares a recap in the background. Reports explain the evidence, a possible mechanism and a repeatable practice experiment. They include clean-lap pace, reported tire snapshots and abrupt brake-release/throttle/steering event counts. These input thresholds are heuristics; they do not establish tire slip, overheating or an inappropriate response to traffic.

Opponent scouting uses CarIdx lap-distance positions to time 40 sections. It requires at least three passages per section from both cars, rejects highly variable timings, and compares medians. The passing call requires a close estimated gap, safe straightaway conditions and no occupied left/right call. It suggests building an exit and considering a pass if clear. It cannot observe opponent steering/pedals, judge their intent or certify a clear passing lane. A repeated pace loss is not proof of a driving mistake. The small sections are generic distance bins, not named corners.

Voice commands added: “Engineer explain that”, “Engineer session recap”, “Engineer passing opportunities”. Explanations refer to the most recently analyzed corner. Local recognition uses the English Windows grammar; online conversation is optional.

Tire-information reference: https://support.iracing.com/support/solutions/articles/31000167257-black-box-screen-information-and-controls . The official tire-info description concerns temperatures/wear of tires removed from the car. This app preserves reported/pit freshness caveats instead of presenting them as live measurements.
