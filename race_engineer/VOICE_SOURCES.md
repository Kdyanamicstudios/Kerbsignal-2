# Free natural voice work

Supertonic 3 (Supertone Inc.) is the new local preset engine. Five male English presets are selectable. Model revision3cadd1ee6394adea1bd021217a0e650ede09a323 is pinned by SHA256; model license is OpenRAIL-M and example inference code is MIT. Full licenses and source metadata accompany the package. The model runs on CPU with two inference threads and does not send speech/telemetry to a service. These are synthetic voices, not recorded human engineers.

American Michael and British George (Kokoro) remain selectable. Existing explicit voice choices are retained across updates; the new default for a fresh profile is Natural M2.

Short driving and spotter calls are rendered in advance, trimmed for audible onset, and validated. The new engine initially produced silent very-short clips at an aggressive speed; the preparation pipeline now uses a more natural speed, retries/rejects silent output, and validates all completed clips. No silent clip is shipped. Physical audio timing and subjective voice quality still need Windows/user listening tests.

Three roughly 13-second preview clips were generated. In this Linux CPU environment a 13.1-second M2 sample took 2.95 seconds at the initial 5-step benchmark. Final 8-step generation prioritizes reading stability. This is not a Windows/iRacing performance guarantee.

ElevenLabs was reviewed as requested. Its official pricing lists 10,000 monthly free credits; it is not unlimited free live coaching. No account, API key or paid service was provisioned. This development build uses the free local pack instead of making ElevenLabs mandatory.

A verified reusable recorded Australian male engineer pack is still unavailable to this project. Presets are not relabeled with an unsupported accent. Optional online Australian delivery remains a style request.

Primary sources reviewed October 30, 2026:
- https://huggingface.co/Supertone/supertonic-3
- https://huggingface.co/Supertone/supertonic-3/blob/3cadd1ee6394adea1bd021217a0e650ede09a323/LICENSE
- https://github.com/supertone-oss-archive/supertonic
- https://elevenlabs.io/pricing
- https://elevenlabs.io/docs/overview/administration/billing
