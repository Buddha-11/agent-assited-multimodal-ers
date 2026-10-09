# Affect · Conversation Lab

**Personalized Agentic Multimodal Emotion Recognition Through Adaptive LLM Conversations**

A local university research prototype built with React/TypeScript, Vite, Tailwind, shadcn-style Radix components, lucide-react, Recharts, FastAPI, SQLAlchemy, SQLite, FFmpeg, faster-whisper, SpeechBrain, and DeepFace. One deterministic Python workflow calls one configurable LLM. No service orchestration, vector database, or recursive agents.

Users can speak with microphone-only or combined camera/audio recordings, or type without media access. The agent receives the actual transcript, independent classifier evidence, recent conversation, confirmed memories, and explicit corrections. Measurements are always uncertain interpretations. Missing inputs have no fabricated scores; conflicting classifier labels produce `mixed_signals` without a combined confidence.

## Run the project yourself (Windows PowerShell)

### Everyday startup on this computer

The dependencies and local configuration have already been installed on this computer. You normally only need these steps; do not reinstall packages or overwrite `backend/.env` each time.

1. Open the project folder in VS Code. Choose **Terminal > New Terminal** and use **PowerShell**.
2. In the first terminal, go to the repository root and start the backend:

   ```powershell
   Set-Location -LiteralPath 'C:\Users\ASUS\Documents\GitHub\Multimodal Emotion'
   .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
   ```

   Keep this terminal open. Wait for **Application startup complete** and the address `http://127.0.0.1:8000`. Using the virtual environment's Python directly means you do not need to activate it. Run the backend from the repository root so it uses the correct database location.

3. Open a **second PowerShell terminal** using the terminal **+** button, then start the frontend:

   ```powershell
   Set-Location -LiteralPath 'C:\Users\ASUS\Documents\GitHub\Multimodal Emotion\frontend'
   npm run dev -- --port 5173 --strictPort
   ```

   Keep this terminal open too. Wait for Vite to show `http://127.0.0.1:5173/`. `--strictPort` prevents Vite from silently choosing a different port if 5173 is occupied.

4. Open **http://127.0.0.1:5173/** in Chrome or Edge. Both terminals must remain running while you use the app. The frontend forwards API requests to the backend on port 8000.
5. Start a conversation and send a typed response first to check the Groq connection. Then enable **Mic**, allow browser microphone access, and speak while watching **Microphone check**. The bars should move. Select the correct microphone if necessary, then use **Test microphone · 5s** and play back the local clip. This test is not uploaded.
6. Once you can hear yourself in the test, press **Record response**, speak for several seconds, and press **Stop & send**. Enable **Camera** if you also want facial analysis; keep one face visible. The first media response after startup may take longer because models load lazily. Missing checkpoints download on first use, so keep an internet connection available.

### Check that startup worked

Open **http://127.0.0.1:8000/docs** to check that the backend is reachable. In an optional third PowerShell terminal, run:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/api/health' | ConvertTo-Json -Depth 6
Invoke-RestMethod 'http://127.0.0.1:8000/api/models/status' | ConvertTo-Json -Depth 6
```

Models can initially be configured but not loaded; they become ready after their first successful use. Health status alone does not verify that Groq accepted your API key. A successful typed conversation verifies that connection.

### Stop the project and resume later

1. Finish or cancel any recording and stop microphone/camera access in the app. Close the app tab.
2. Click the **frontend terminal** and press **Ctrl+C**. If PowerShell asks whether to terminate the batch job, type `Y` and press Enter.
3. Click the **backend terminal** and press **Ctrl+C**. Wait for shutdown to complete and the PowerShell prompt to return.

Closing the browser alone does not stop the servers. Stopping the servers preserves the SQLite database at `data/emotion_agent.db`, the model caches, and `backend/.env`. The next time you want to work, repeat **Everyday startup** above. Do not delete these files to stop the project. Restart the backend after changing `backend/.env`.

### First-time installation or setup on another computer

Follow this section only if the virtual environment or frontend dependencies are missing, or you are setting up a fresh checkout. Update the absolute paths above if your checkout is in another folder.

Check the prerequisites in PowerShell:

```powershell
py -3.10 --version
node --version
npm --version
```

Use **Python 3.10** and **Node 22 / npm 10** for the verified setup. Install them first if the commands are missing, then reopen your terminal. Python 3.14 is not supported by the pinned ML stack. From the repository root, install the dependencies:

```powershell
Set-Location -LiteralPath 'C:\Users\ASUS\Documents\GitHub\Multimodal Emotion'
.\scripts\setup.ps1
```

The script creates `.venv` if needed, installs backend/ML dependencies, creates `backend/.env` only if it is missing, and runs `npm ci` in `frontend`. Downloads can take time; wait for **Setup complete**. If PowerShell blocks script execution, use the manual commands in the next section instead.

Open `backend/.env` in your editor and configure the Groq values shown below. Keep your own API key in this local file. Then follow **Everyday startup**. The normal setup needs no separate database server, database migration command, or system FFmpeg installation; SQLite and the bundled FFmpeg binary handle these requirements.

### Troubleshooting startup and recording

| Symptom | Steps to follow |
|---|---|
| `.venv\Scripts\python.exe` is missing, or Python reports a missing package | From the repository root, run the setup script or manual installation below. Use `.venv` Python for the backend rather than a global Python installation. |
| `npm` is not recognized | Install Node.js, reopen PowerShell, and check `node --version` and `npm --version`. |
| Frontend opens but API requests fail | Confirm the backend terminal says startup is complete and `http://127.0.0.1:8000/docs` opens. Keep both servers running. |
| Groq reports an authentication error or session creation fails | Check `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` in `backend/.env`, then restart the backend. Do not put the key in frontend code. |
| Groq reports a rate limit | Wait for the provider's quota to reset before retrying; restarting the app does not reset the quota. |
| PostCSS reports a missing `jiti` module | Stop the frontend with Ctrl+C. In the `frontend` folder run `npm ci`, then `npm run dev -- --port 5173 --strictPort`. Refresh the browser. Restart Vite after reinstalling dependencies so it does not keep old module paths in memory. |
| Port 8000 or 5173 is already in use | Stop the earlier project terminal with Ctrl+C, then start again. Do not start duplicate servers. Keep these default ports because the frontend proxy expects backend port 8000. |
| Microphone permission is denied | In the browser's site permissions for `127.0.0.1`, allow microphone access, then enable Mic again. In Windows **Settings > Privacy & security > Microphone**, allow microphone access for desktop apps. |
| Bars do not move or the recording is silent | Select the correct input in **Microphone check**, check the headset mute switch, and check Windows **Settings > System > Sound > Input** for the chosen device and input volume. Use the five-second local test and listen to playback before sending a response. If the meter is paused, click **Resume input meter**. |
| Recording is too short or no transcript is found | Record several seconds of clear speech after confirming the bars move. Stop only after speaking. You can also type a response. |
| Models fail on first media use | Check internet access and the backend log for the failing download/package. After fixing the cause, restart the backend so failed model initialization can retry. |

## Manual installation and provider configuration

Prerequisites: **Python 3.10** and **Node 22 / npm 10**. Python 3.14 is not supported by the pinned ML stack. Run commands from the repository root.

```powershell
./scripts/setup.ps1
```

If script execution is restricted, use these equivalent commands in your shell:

```powershell
py -3.10 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r backend/requirements-ml.txt
if (-not (Test-Path -LiteralPath 'backend/.env')) {
    Copy-Item -LiteralPath 'backend/.env.example' -Destination 'backend/.env'
}
cd frontend
npm ci
cd ..
```

Copy the environment example only when `.env` does not already exist. The setup script preserves existing configuration. For text-only development use `./scripts/setup.ps1 -CoreOnly`; missing ML packages appear as unavailable in diagnostics.

Edit **backend/.env** locally:

```dotenv
LLM_API_KEY=your-provider-key
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-20b
LLM_RESPONSE_FORMAT=json_schema
LLM_REASONING_EFFORT=low
LLM_MAX_OUTPUT_TOKENS=1200
```

The current local configuration uses **Groq's `openai/gpt-oss-20b`** with the supplied key stored only in the ignored `backend/.env`. The example contains no credential. [Groq's compatible endpoint](https://console.groq.com/docs/openai) supports the existing HTTP provider abstraction. [Strict structured output](https://console.groq.com/docs/structured-outputs) validates the response schema at the provider; Pydantic additionally validates it locally. Reasoning output is excluded, reasoning effort is low, and the 1200-token cap leaves room for reasoning and final JSON. Free-tier quota exhaustion returns a clear rate-limit diagnostic; no paid service tier is explicitly requested.

For other compatible providers choose `LLM_RESPONSE_FORMAT=json_object` if strict JSON Schema is unsupported and leave `LLM_REASONING_EFFORT` unset if unsupported. Local servers can use `LLM_REQUIRE_API_KEY=false`. Creating a session returns a diagnostic 503 if no usable key/model is configured. Keep keys exclusively in backend environment variables.

Start the backend in one terminal:

```powershell
./.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend in another:

```powershell
cd frontend
npm run dev -- --port 5173
```

Open **http://127.0.0.1:5173/**. API documentation: **http://127.0.0.1:8000/docs**. Keep one backend worker: inference capacity and session locks are process-local. The Vite proxy sends `/api` requests to localhost:8000. All startup commands bind to localhost. Stop each terminal with Ctrl+C. Restart the backend after editing `.env`.

## Architecture

```text
Browser MediaRecorder → multipart upload → FastAPI worker thread
  → bounded FFmpeg decoding → mono 16 kHz WAV + frames sampled at 1 fps
  → faster-whisper transcript
  → SpeechBrain acoustic classifier + DeepFace expression classifier
  → independent evidence fusion
  → recent history + confirmed SQL memories + user feedback
  → one OpenAI-compatible structured LLM completion
  → transactional SQLite messages/evidence + React reply/timeline
```

All API handlers performing synchronous work are FastAPI `def` handlers, executed in the worker thread pool. Models load lazily once per process with initialization locks. A global nonblocking semaphore admits one inference job. Session mutation locks reject overlapping turns, ending, and deletion with 409. If the LLM fails, no partial conversation turn is committed. The browser retains an unsent recording for an explicit retry until success, discard, or navigation to another session.

Raw uploads and extracted frames live in generated temporary directories and are deleted in success and error paths. The upload filename is ignored. Decoding uses argument arrays with `shell=False`, bounded processing time, size and duration checks, and no raw-recording API. Browser WebM streams without duration metadata are decoded over a bounded interval to measure their actual duration. Multipart uploads use Starlette's spooled upload storage; the application copies in 1 MB chunks.

## Interface and consent

The dark dashboard includes chat, a camera panel, separate acoustic/facial cards, Recharts timelines, session history, profile/memory controls, feedback dialogs, settings, and model status. A participant ID and optional device/language/speech preferences are stored in browser localStorage; credentials and media are not.

1. Begin a conversation after configuring the LLM.
2. Enable **Camera** for audio/video or **Mic** for audio only. Browser permission is requested on this action, never on page load.
   The **Microphone check** panel shows the connected device name and 20 live level bars. Speak normally and confirm the bars move before recording. Select another input directly in the panel if needed; the selection is saved with your browser preferences. Sound activity is not a speech/emotion classification.
   Use **Test microphone · 5s**, speak, then play the local clip to confirm that your voice reaches the recording encoder. Test clips remain in this tab, are never uploaded, and can be discarded. Releasing devices, switching inputs/sessions, or leaving the page clears the clip. A paused analyser has an explicit **Resume input meter** button. If bars remain flat, check the headset mute switch and Windows input volume.
3. Press **Record response**, speak, then **Stop & send**. The recording stops at the configured limit. Cancel discards the recording.
4. The transcript becomes your message. Model scores and the contextual agent reply appear after processing.
5. Open **View analysis & give feedback** or a message's compact evidence summary to confirm, correct, decline, or mark unsure.
6. Confirm or edit proposed memories in **Profile & memory**. Unconfirmed proposals never enter agent context. Add explicit preferences directly if desired.

Turning the camera off releases all input tracks; microphone-only access can then be enabled separately. Switching sessions, ending a session, or destroying the recorder releases tracks. Hiding the preview only hides it and does not stop active media. Device selections take effect when access is re-enabled. Typed turns skip all media inference. Audio permission denial can be handled by typing; camera denial can be handled by enabling Mic alone.

Disabling memory excludes confirmed memories and past-session corrections from future calls and stops new proposals. Messages and current-session feedback still support the active conversation. Deleting history removes sessions, messages, observations, feedback, and all memories. Deleting an individual session leaves separately confirmed user memories; manage those in the profile.

## Models and execution

| Integration | Implementation | Checkpoint / output |
|---|---|---|
| Transcription | `backend/app/models/transcription.py` | `faster-whisper` base, CPU int8 by default; VAD and no-speech/log-score filters; language and segments |
| Acoustic emotion | `backend/app/models/audio_emotion.py` | `speechbrain/emotion-recognition-wav2vec2-IEMOCAP`; checkpoint `ind2lab` read at runtime |
| Facial expression | `backend/app/models/face_emotion.py` | DeepFace Emotion model, OpenCV detector, enforced face detection, single subject per sampled frame |
| Conversation | `backend/app/agent/conversation_agent.py` | OpenAI-compatible HTTP client; Pydantic-validated JSON; one request per opening/turn |

SpeechBrain 1.0.3's installed `speechbrain.inference.interfaces.foreign_class` API was inspected and exercised. The [checkpoint's official custom class](https://huggingface.co/speechbrain/emotion-recognition-wav2vec2-IEMOCAP) is `CustomEncoderWav2vec2Classifier` in `custom_interface.py`. Windows uses `LocalStrategy.COPY` to avoid administrator symlink requirements. The measured mapping was **0→neu, 1→ang, 2→hap, 3→sad**. Original labels and scores are preserved. The frontend expands their names for readability; fusion maps only semantically equivalent labels. Scores are not calibrated probabilities or guarantees of an internal emotional state.

[DeepFace](https://github.com/serengil/deepface) uses `analyze(actions=['emotion'], enforce_detection=True)`. Frames with no face are excluded. Frames with multiple faces are flagged ambiguous and excluded; no identity tracking is claimed. Scores are converted from the model's percentage scale to 0–1 and averaged only across valid frames from the same classifier. DeepFace runs on CPU independently of SpeechBrain.

[faster-whisper](https://github.com/SYSTRAN/faster-whisper) uses VAD, rejects no-speech segments, and disables previous-text conditioning. This reduces silence hallucinations but is not an absolute guarantee on noisy recordings. Silent/short or empty-transcript media requests ask for a retry or typed reply. Facial/audio classifier failure preserves other available evidence; transcription failure prevents a speech-driven turn and directs the user to text input.

Model caches live in `.cache/`; SpeechBrain's upstream wav2vec2 base cache also uses `wav2vec2_checkpoints/`. Both are ignored by git. First inference downloads checkpoints and can be slow. Restart after fixing a failed model initialization. Diagnostics distinguish installed/configured, loading, ready, unavailable, and failed; configured does not imply verified connectivity.

### CPU / CUDA

The verified environment uses CPU PyTorch and CPU int8 Whisper. NVIDIA hardware was detected, but CUDA inference was not validated. CPU inference is functional and avoids CUDA runtime setup for the deadline.

For optional SpeechBrain GPU acceleration, install the matching official PyTorch/torchaudio CUDA wheels into the same environment, for example:

```powershell
./.venv/Scripts/python.exe -m pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
```

Set `AUDIO_DEVICE=auto` or `cuda`. If CUDA is unavailable, SpeechBrain falls back to CPU; load-time CUDA out-of-memory also retries on CPU. Whisper GPU mode additionally requires compatible CTranslate2, CUDA/cuBLAS and cuDNN runtime libraries; follow the linked faster-whisper installation guide, then set `WHISPER_DEVICE=cuda` and `WHISPER_COMPUTE_TYPE=float16`. Leave Whisper on CPU if runtime libraries are missing. Do not set `CUDA_VISIBLE_DEVICES=-1` when expecting SpeechBrain CUDA.

### FFmpeg

`imageio-ffmpeg` supplies a Windows FFmpeg binary, verified for extraction and duration validation. No system installation is necessary in this environment. Alternatively install a trusted FFmpeg distribution and add it to PATH, or set `FFMPEG_PATH` to its executable. The app uses FFmpeg, not an ffprobe dependency.

## Configuration

See `backend/.env.example` and `frontend/.env.example`.

| Setting | Default / use |
|---|---|
| `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` | Secret, compatible `/v1` endpoint, provider model identifier |
| `LLM_REQUIRE_API_KEY` | `true`; set false only for a server that does not require authentication |
| `LLM_TEMPERATURE` / `LLM_MAX_OUTPUT_TOKENS` / `LLM_TIMEOUT` | Groq environment example: `0.7` / `1200` / `45` seconds |
| `LLM_RESPONSE_FORMAT` / `LLM_REASONING_EFFORT` | Groq: `json_schema` / `low`; generic provider fallback: `json_object` / unset |
| `WHISPER_MODEL` / `WHISPER_DEVICE` / `WHISPER_COMPUTE_TYPE` | `base` / `cpu` / `int8` |
| `AUDIO_EMOTION_MODEL` / `AUDIO_DEVICE` | Official SpeechBrain IEMOCAP checkpoint / `auto` |
| `FACE_FRAME_INTERVAL` | `1` second; configurable bounded sampling interval |
| `DATABASE_URL` | `sqlite:///./data/emotion_agent.db`; run from repository root |
| `MAX_RECORDING_SECONDS` / `MAX_UPLOAD_MB` | `30` seconds / `25` MB |
| `CORS_ORIGINS` | JSON array of local frontend origins |
| `FFMPEG_PATH` | Optional executable path; otherwise system/bundled binary |
| `HF_HOME` / `DEEPFACE_HOME` | Local ignored model-cache directories |
| `VITE_API_BASE` | Optional backend URL; empty uses Vite proxy |

The settings UI changes model name, temperature, and output length for the current process only. It does not expose credentials or rewrite `.env`. Invalid provider JSON returns a clearly identified formatting-retry response with no memory candidate. HTTP failures/timeouts return 503 and do not pretend to be successful agent responses. Full server exceptions are logged locally; browser errors are sanitized.

## API

Every endpoint has a Pydantic request/response schema. See `/docs` for detailed fields.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/users` | Create local demo participant |
| GET / PATCH | `/api/users/{id}/profile` | Profile/name/retention controls |
| POST | `/api/users/{id}/memories` | Add explicit confirmed statement |
| PATCH / DELETE | `/api/users/{id}/memories/{memory_id}` | Edit / remove memory |
| POST | `/api/users/{id}/memories/{memory_id}/confirm` | Confirm agent proposal |
| DELETE | `/api/users/{id}/history` | Delete participant history and memories |
| POST / GET | `/api/sessions` | Start session / list by `user_id` query parameter |
| GET / DELETE | `/api/sessions/{id}` | Retrieve / delete session |
| POST | `/api/sessions/{id}/turns` | Multipart `media`, `consent=true`, optional language code |
| POST | `/api/sessions/{id}/text-turns` | JSON text reply |
| POST | `/api/sessions/{id}/feedback` | Confirm/correct/unsure/decline by observation ID |
| POST | `/api/sessions/{id}/end` | End conversation |
| GET | `/api/sessions/{id}/analytics` | Chronological observations and feedback |
| GET | `/api/health`, `/api/models/status` | Integration diagnostics |
| GET / PATCH | `/api/settings` | Safe runtime provider settings (no credentials) |

SQLite tables: users, sessions, messages, emotion_observations, emotion_feedback, user_memories. Foreign-key cascades delete related interaction data. Feedback updates a single record per observation. Memories are explicit confirmed statements or proposals requiring confirmation; model evidence is never silently promoted to a permanent personality fact.

## Tests and real verification

```powershell
./.venv/Scripts/python.exe -m pytest backend/tests -q
./.venv/Scripts/python.exe -m pip check
cd frontend
npm run build
npm run typecheck
npm run test:audio
npm audit
cd ..
./.venv/Scripts/python.exe scripts/verify_models.py
```

Unit tests mock the LLM and selected model failures. They cover health/configuration, users/sessions, typed turns, rollback on provider failure, invalid provider JSON, missing/invalid media, real FFmpeg extraction, no audio, no face, ambiguous faces, silence, disagreement, memory persistence and retention, feedback updates, overlap rejection, retrieval, deletion, and evaluation CSV/metrics arithmetic. Unit fixtures are not benchmark datasets.

The separate smoke script uses actual downloaded checkpoints and public maintainer samples. It creates a five-second test WebM combining an official audio example with a static official DeepFace test image; this verifies the media/perception integration, not synchronized human emotional agreement. Raw samples remain ignored locally. Recorded evidence is in **`output/verification/real-model-smoke.json`**, including actual outputs, checkpoint labels, API signature, and measured timings. No dataset accuracy or F1 benchmark is claimed.

Verify the current real media → LLM → database API loop:

```powershell
./.venv/Scripts/python.exe scripts/verify_models.py --llm
```

Verify a contextual text conversation against the running frontend's API proxy:

```powershell
./.venv/Scripts/python.exe scripts/verify_groq.py --base-url http://127.0.0.1:5173
```

Both Groq smoke tests have passed with actual provider calls. See `output/verification/groq-conversation-smoke.json` and the media report. The backend regression suite currently has 23 passing tests; those unit tests remain separately mocked. Three microphone-meter tests check the waveform calculation; live hardware still requires the browser check.

To verify your own consenting recording:

```powershell
./.venv/Scripts/python.exe scripts/verify_models.py --media path/to/recording.webm
```

Personal-media reports go to ignored `output/private/`. Do not commit raw media, database files, credentials, or personal transcripts. The optional LLM smoke run creates disposable test conversation data and deletes its history afterward.

### Manual browser smoke checklist

Live hardware/browser capture has not been verified by automation in this environment because no browser is connected to the browser-control tool. Verify in Chrome/Edge/Firefox at localhost:

- Start a session, type a project-related message, and check a contextual provider reply.
- Enable Mic only, record speech, stop, and check transcript + acoustic evidence + reply.
- Enable Camera, record speech with one visible subject, and check separate audio/facial scores.
- Cancel a recording; verify it is not uploaded. Stop devices; verify the browser's capture indicator clears.
- Deny camera permission, enable Mic alone, then test denied microphone permission with typed input.
- Correct an interpretation, refresh the session, and check saved feedback.
- Confirm a practical-response preference, start another session, and inspect agent behavior.
- Toggle retention, edit/delete memories, and delete disposable session/history data.
- Reload the browser; check participant/session restoration. Test mobile width and keyboard navigation.

## Evaluation and research extension

`backend/evaluation/metrics.py` computes accuracy, macro/weighted F1, macro precision/recall, confusion matrix, and classification report from supplied real ground-truth and predicted labels. `export_predictions()` writes the labels and model provenance to CSV. No benchmark was generated or measured.

Replace `PerceptionPipeline` in `backend/app/services/perception.py` or implement `FusionStrategy` in `backend/app/services/fusion.py` for later [COGMEN](https://github.com/Exploration-Lab/COGMEN), [DialogueCRN](https://github.com/zerohd4869/DialogueCRN), or [MERBench/MERTools](https://github.com/zeroQiaoba/MERTools) work. Keep the normalized `Evidence` contract, return original labels/scores with model provenance, and separately evaluate each research checkpoint. Dialogue-conditioned research models require alignment, dataset-specific inputs, and label validation; they are intentionally not implemented here.

## Practical limits

- This is a localhost demo without authentication, authorization, or multi-user isolation. Participant IDs identify records but are not security credentials. Do not expose it publicly without adding access control and request limits.
- Real Groq/GPT-OSS 20B conversation and media-to-LLM API smoke tests are recorded in `output/verification/`. Unit tests separately use mocked provider responses. Live browser hardware capture still requires the manual checklist.
- CPU inference and downloads can be slow. GPU paths are configurable but not validated on this installation. The first model call warms caches; diagnostics make loading visible.
- Classifier outputs are dataset-dependent and uncalibrated. SpeechBrain's checkpoint is trained on English IEMOCAP; multilingual transcription does not make acoustic emotion accuracy multilingual.
- The face MVP excludes multiple faces and does not track identity. A static-image smoke test is not a realistic camera evaluation.
- Browser-request cancellation aborts the client fetch; already-running server inference may finish. Refresh the session before retrying; concurrent mutation is rejected. Full server job cancellation and resumable uploads are not implemented.
- Ending/deleting a session during processing returns 409; wait for the active turn. History deletion also refuses concurrent session mutation.
- No persistent raw-recording retention option is enabled. Session summary is optional and currently unset; messages and evidence remain fully reviewable.
- Browser speech synthesis is optional and depends on browser/OS voices. Fonts load from Google Fonts with local fallbacks.
- Retention controls govern long-term personalization; conversation storage is managed through the separate deletion controls.

Dependency installation and reproducible local inference were verified on Windows with Python 3.10. Package-level deprecation warnings from upstream SpeechBrain/TensorFlow/Starlette can appear in logs. The installed Windows dependency snapshot and verification report document this environment.
