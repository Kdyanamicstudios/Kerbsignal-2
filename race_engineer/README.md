# KerbSignal 0.13

Your Windows iRacing engineer. Formerly Race Engineer.

## Install and start

Close the previous app, then open **KerbSignal.exe**. It installs for your
Windows user and creates an **KerbSignal** desktop and Start menu shortcut.
You do not need Python or build tools. Requires 64-bit Windows 10/11.

The existing install and data locations are retained so an upgrade keeps your
settings and lap history. Program files live under
`%LOCALAPPDATA%\Programs\RaceEngineer`; user data remains in
`%LOCALAPPDATA%\RaceEngineer`. Do not delete the data folder to upgrade.

On first launch, follow the nine-step tutorial. Replay it from Settings or
Tutorial. Join an iRacing session and get in the car: the app connects
automatically. Confirm the car, exact track/layout and telemetry status.
Synthetic demo is a separate mode and never a live-session fallback.

## What changed in 0.13

- Replaced the old screen arrangement with a fixed left navigation rail and
  a full-width native driving workspace. Drive, Analyze, Racecraft, Garage,
  Engineer, Settings and Help are always named in the rail.
- G-FORCE now has its own large panel beside the real circuit map. The
  3 g circle shows lateral/longitudinal acceleration, resultant g and a short
  trace. It remains visible while disconnected, with no fabricated live dot.
- Lap timing, best lap, delta, mph and gear occupy the top strip. The engineer
  instruction spans the page, followed by the map/G-circle and a full-width
  speed, brake, throttle and steering graph. The driving page does not scroll.
- Technical details and the radio transcript have their own Engineer page.
  Existing users start on Drive; an incomplete tutorial no longer changes
  pages on every launch. New users still receive the first-run tutorial.
- New logo and startup animation, light/dark appearance, scrolling fixes,
  connection state tied to fresh valid iRacing data, and overlay widths from
  160 pixels are included.
- Five local Supertonic 3 male voices join the American/British Kokoro voices.
  All 126 short coaching/spotter clips were checked for audible signal and
  duration. The larger download includes local models; no account or online
  voice quota is required. Speech remains synthetic.
- Practice, qualifying and race awareness; pit-lane/box/service/exit detection;
  saved pit recaps; varied information tied to telemetry events; and Quiet,
  Standard or Chatty radio modes are included. Traffic and timed calls have
  priority. Tire/service claims remain limited to observed telemetry.
- Native IBT reference import validates a complete clean lap and recorded
  SDK identity/time. Universal expert-lap coverage remains unavailable.
- The updater supports verified resumable downloads. Public access to the
  release feed is awaiting authorization, so install this update directly.

This is a Windows test build. Automated flow checks and native dependency
checks do not replace a launch, physical-device or live-iRacing test.

## Straightaway briefings

Settings → General includes detailed straightaway briefings. On a suitable
straight, the engineer can announce distance in meters and estimated seconds
to the next aligned braking zone, a learned/guide-authored turn description,
and estimated gaps ahead and behind. The same information remains visible
under the main coach banner. Full detail is spoken only when the remaining
straight allows time before the countdown; shorter straights get shorter
briefings. Each target corner is announced at most once per lap, with a
25-second minimum interval. Traffic and precisely timed calls always preempt.

Turn direction/shape is an estimate from a matching reference GPS trace or
explicit guide metadata. Missing geometry is labeled unknown. The displayed
reference minimum speed is an observation, not an instruction to achieve that
speed in different conditions. Distances follow spatial markers, not a guessed
lap duration. No braking-distance briefing is invented without markers.

## Hear useful coaching

In Settings → Voice & audio, choose a free voice, device and volume; save,
then test the engineer and the short timed brake sample. The offline free
voices are Supertonic 3 male presets and Kokoro Michael/American and George/British,
not recorded humans. An Australian pack is not bundled. Optional installed
Windows voices and online conversation remain in Advanced voice options.
Those advanced voices use their own system audio path; the output/volume
selection applies to free neural speech and timed calls.

Automatic coaching starts when fresh telemetry confirms forward driving.
Pause/resume it on Drive or in Settings. Settings independently controls the
spotter, session reports, input feedback, detailed reviews and praise.
Microphone starts off. Enable it for commands such as:

- Engineer what car am I driving
- Engineer what track am I on
- Engineer where am I on track
- Engineer tires / Engineer weather
- Engineer enable braking cues / Engineer disable braking cues
- Engineer where am I losing time
- Engineer play focus music (opens your saved YouTube link)
- Engineer mute / Engineer unmute

The built-in microphone uses installed Windows English recognition and defined
commands. Free-form online voice is optional, requires your own API key and
sends the spoken turn plus current telemetry snapshot when connected. Local
history does not store microphone audio.

### Corner markers are essential

Input observations and session information can work immediately. Exact
brake/turn/throttle calls require either an aligned position guide for the
actual car/layout or a complete clean driving trace. The engineer banner explains whether
calls are learning, ready, paused by conditions, or waiting for audio.

In Corner guides, import a matching guide or record/capture the distance
markers for each corner. Learned markers reproduce observed inputs; they are
not proof of the fastest or optimal line. A faster, clean reference from the
same profile/conditions can improve comparisons. Garage 61 import remains
optional and limited to records the user's token can access.

There is no verified fastest-lap / video-aligned marker library for every
car/layout. Coaching-video sources are linked, but a video timestamp is not a
simulator braking coordinate. Align landmarks before using them as a guide.

### Timing calibration

Audio lead is adjustable in Settings → Voice & audio and Corner guides.
Start with the saved value (150 ms on a fresh profile). If the prompt reaches
you late, add 50 ms; if early, subtract 50 ms. This lead includes output and
reaction preference. Verify in solo practice on the exact car/layout. Changing
lead does not repair an incorrect spatial landmark.

Traffic calls preempt corner calls. Longer feedback, gap reports and praise
wait for straights and yield to critical instructions. Pits, replay, caution,
stale/invalid position, changed guide conditions or incomparable reference
speeds can pause corner calls. The app does not invent instructions when data
is missing. It does not perform traffic-aware path planning or control inputs.

If calls are wrong or absent, save diagnostics on Drive. The JSON includes
metadata, marker/position details, played/suppressed cue history and estimated
audio onset/latency. It excludes API keys and microphone audio. Send it with
the exact car/layout and selected output device for investigation.

## Timer, map and overlay

CURRENT LAP comes from iRacing's live lap clock. It does not run from a guessed
reference lap duration. The delta is shown only when the SDK declares it valid.
Best time uses the simulator's session best where available, or your recorded
clean best; imported third-party reference time is not displayed as your PB.

The graph shows MPH and brake/throttle inputs. Physics/import data remains in
SI units internally. The map uses observed SDK GPS; a learned route plus live
lap distance can supply estimated XY when GPS is missing/frozen. The outline
needs a drive around the layout or a suitable imported route. Lap progress and
meters from the start remain available without a complete outline. Stale
position is marked; the app does not fabricate a known track shape.

Use borderless/windowed iRacing for the overlay. Exclusive fullscreen and VR
are not supported. In Settings → Overlay, choose 240–1200 px width, opacity,
and lock state. Drag while unlocked; lock enables click-through. Unlock/reset
from Settings. Existing old-format overlay preferences migrate to 360 px.

The circle plots reported lateral/longitudinal acceleration divided by
9.80665 m/s² per g. Braking is at the top; acceleration is at the bottom.
The ring radius represents 2 g; values beyond it are clipped spatially while
the numeric magnitude remains visible. It excludes vertical acceleration and
is not a grip or tire-temperature sensor. Missing acceleration displays G —.

## Situational reports and controller detection

Session type is read from iRacing. Practice/out-lap advice to build tire and
brake temperature is guidance, not a claim of measured cold temperatures.
Tire data may be pit-updated; live brake temperature is not available in this
implementation. The app explicitly labels unavailable/delayed temperatures.

Relative traffic reports estimate passage-time gaps at common track positions.
They need an observation history, reset after missing data/pits/teleports,
and identify physically nearby cars, not necessarily adjacent race positions.
Trend messages state the gain over their measured time window. They are not
claimed to match iRacing's official F3 gaps exactly. No report is invented when
opponent position channels or sufficient history are unavailable.

Settings → Devices enumerates attached Windows HID/game controllers without
changing calibration or force feedback. Names/roles depend on drivers; role
suggestions are heuristics. Pedals connected through a wheel base may appear
as one combined device. Use assignment menus to correct roles. This detects
connected hardware, not iRacing's private active-controller binding.

## Review, setup and music

Lap history keeps real and synthetic sessions separate. Select a clean lap to
review its time and line or export a reference. Racing-line proximity alone
is not proof that a line is faster.

Setup lab supports baseline/test laps with a recorded single change and
comparison controls. Recommendations are conditional on the detected car and
available telemetry; fixed setups and unavailable intervention/slip data limit
what can be concluded.

Focus music opens your chosen YouTube link in your browser. Browser autoplay
may still require Play. The app does not download or redistribute music.

## Updates and validation

The app has update checking/download/verification plumbing and a persistent
installer, but no maintained hosted release channel is configured. Automatic
update delivery is still unavailable. Installing a newer release preserves the
separate history/settings data. No declined account integration is required
for ordinary app use.

Automated tests cover coaching, output buffering, gap estimation, preferences,
tutorial state and hardware role suggestions. Static native dependency and
installer integrity checks are performed for the release. Real Windows/iRacing
launch, device identification, overlay behavior and physical speaker timing
cannot be certified from the Linux build environment.

Developer source and third-party licenses/corresponding sources are included
in the source bundle and installer. The bundled build scripts can restore the
runtime from a prior release using official 7-Zip when the original download
cache is absent. These developer steps are not required to use the app.


See FEATURE_REVIEW.md for the new Training and Racecraft tabs, microphone test, map coverage, steering analysis and remaining limitations.
