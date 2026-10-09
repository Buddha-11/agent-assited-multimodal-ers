# Verification record

Verified on 9 October 2026 in the local Windows workspace using Python 3.10 and Node 22.

- Backend tests: **23 passed**. Tests mock the LLM and selected model paths; FFmpeg extraction and decoding tests use the actual bundled executable. Groq request-format, rate-limit diagnostics, and specific short-recording guidance are also tested. One upstream Starlette/AnyIO deprecation warning remains.
- Microphone meter tests: **3 passed**, checking silence, actual waveform RMS, display scaling, and dBFS calculation. These exercise arithmetic, not live hardware capture.
- Frontend production build and TypeScript check: passed.
- Frontend `npm audit`: **0 reported vulnerabilities** after upgrading Tailwind.
- Python `pip check`: no broken requirements.
- Local HTTP checks: frontend and backend health both returned 200.
- The updated microphone component, recorder module, and meter stylesheet return 200 from the live Vite server. A new production build passes. The meter displays 20 input-level bars, the connected device name, an input selector, and a five-second local playback test without uploading that clip.
- Real downloaded Whisper, SpeechBrain, and DeepFace checkpoints: successful inference. See `real-model-smoke.json` for measured output, label mapping, and runtime details.
- Real perception workflow: transcript, independent audio/facial scores, and disagreement aggregation returned successfully.
- Real Groq/GPT-OSS 20B opening and typed turns passed through the running frontend's API proxy at localhost:5173. `groq-conversation-smoke.json` records contextual replies and successful persistence without mocked provider calls.
- Real media-to-LLM API turn returned 200 using actual checkpoints and Groq. `real-model-smoke.json` includes the persisted messages, model evidence, and validated agent reply. Disposable smoke-test histories were deleted afterward.

The public five-second smoke recording combines SpeechBrain's official `anger.wav` sample and a static DeepFace maintainer test image. It does not represent a real synchronized human interaction or a benchmark dataset. Its transcript begins “What can you prove it”; SpeechBrain returned `ang`; DeepFace returned `happy` for five valid sampled frames; aggregation returned `mixed_signals`. Original neural scores are saved and labeled uncalibrated. Model outputs near 1.0 are not accuracy measurements.

SpeechBrain's loaded checkpoint mapping was `0=neu, 1=ang, 2=hap, 3=sad`. CPU inference was verified. NVIDIA RTX 3060 hardware was detected, but installed PyTorch is the CPU build; CUDA inference was not verified.

The local provider is configured as `https://api.groq.com/openai/v1` with `openai/gpt-oss-20b`. Credentials are held only in ignored `backend/.env` and are not included in these reports. Requests use strict JSON Schema, low reasoning effort, a 1200-token completion cap, and exclude reasoning output. Real text and full media-to-LLM API workflows are **verified**. Free-tier quota failures have a clear diagnostic; no paid service tier is explicitly requested.

The browser-control tool reported no connected browsers. Visual layout, live camera/microphone permissions, and actual browser recording have **not been manually or automatically verified** here. Follow the manual browser checklist in the README.
