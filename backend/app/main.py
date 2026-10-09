import logging
import re
import tempfile
from pathlib import Path
from threading import Lock
from contextlib import contextmanager
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, get_db
from .db_models import User, Conversation, Observation, Memory, now
from .schemas import *
from .agent.conversation_agent import agent, AgentUnavailable
from .services import memory
from .services.perception import perception, PerceptionError
from .services.media import process_media, MediaError, ffmpeg_binary

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
Base.metadata.create_all(engine)
app = FastAPI(title='Affect · Emotion Research Agent', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=['*'], allow_headers=['*'])

# One process and a fixed striped lock table bound memory usage. Mutating requests
# sharing a session/user fail quickly rather than queuing overlapping turns.
locks = [Lock() for _ in range(257)]
@contextmanager
def operation(key: str):
    lock = locks[hash(key) % len(locks)]
    if not lock.acquire(blocking=False): raise HTTPException(409, 'Another operation is running. Try again when it finishes.')
    try: yield
    finally: lock.release()

def require(db, model, key):
    row = db.get(model, key)
    if not row: raise HTTPException(404, 'Record not found')
    return row

def active(row):
    if row.ended_at: raise HTTPException(409, 'This session has ended. Start a new conversation.')

def response(db, row, evidence=None, latest=None):
    user = require(db, User, row.user_id)
    history = memory.get_recent_history(db, row.id)
    if latest: history.append({'role': 'user', 'content': latest})
    try:
        return agent.respond(history, evidence.model_dump() if evidence else None,
            [m.content for m in memory.get_relevant_memories(db, user)], memory.recent_feedback(db, user.id, None if user.memory_enabled else row.id))
    except AgentUnavailable as exc: raise HTTPException(503, str(exc)) from exc

def commit_turn(db, row, evidence):
    reply = response(db, row, evidence, evidence.transcript.text)
    human = memory.save_message(db, row.id, 'user', evidence.transcript.text)
    memory.save_emotion_observation(db, row.id, human.id, evidence)
    memory.save_message(db, row.id, 'assistant', reply.response)
    candidate = memory.propose_memory(db, require(db, User, row.user_id), reply.memory_candidate)
    if reply.strategy == 'close_conversation': row.ended_at = now()
    db.commit()
    return TurnOut(session=memory.session_detail(db, row), agent=reply, memory_candidate=candidate)

@app.get('/api/health', response_model=Health)
def health():
    models = perception.status()
    models['llm'] = agent.provider.status()
    try:
        ffmpeg_binary()
        models['ffmpeg'] = Status(state='ready', detail='FFmpeg binary available')
    except Exception:
        models['ffmpeg'] = Status(state='unavailable', detail='Install FFmpeg or imageio-ffmpeg')
    return Health(status='ok', max_recording_seconds=settings.max_recording_seconds, models=models)

@app.get('/api/models/status', response_model=dict[str, Status])
def model_status(): return health().models

@app.get('/api/settings', response_model=RuntimeSettings)
def runtime_settings():
    return RuntimeSettings(model=settings.llm_model, temperature=settings.llm_temperature,
                           max_output_tokens=settings.llm_max_output_tokens, timeout=settings.llm_timeout)

@app.patch('/api/settings', response_model=RuntimeSettings)
def update_runtime_settings(payload: RuntimeSettings):
    settings.llm_model = payload.model
    settings.llm_temperature = payload.temperature
    settings.llm_max_output_tokens = payload.max_output_tokens
    settings.llm_timeout = payload.timeout
    agent.provider.last_status = None
    return runtime_settings()

@app.post('/api/users', response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    row = User(name=payload.name.strip() or 'Research participant')
    db.add(row)
    db.commit()
    return row

@app.get('/api/users/{user_id}/profile', response_model=Profile)
def profile(user_id: str, db: Session = Depends(get_db)):
    return memory.get_user_profile(db, require(db, User, user_id))

@app.patch('/api/users/{user_id}/profile', response_model=Profile)
def update_profile(user_id: str, payload: ProfileUpdate, db: Session = Depends(get_db)):
    with operation(user_id):
        row = require(db, User, user_id)
        for key, value in payload.model_dump(exclude_none=True).items(): setattr(row, key, value)
        db.commit()
        return memory.get_user_profile(db, row)

@app.post('/api/users/{user_id}/memories', response_model=MemoryOut, status_code=201)
def add_memory(user_id: str, payload: MemoryCreate, db: Session = Depends(get_db)):
    user = require(db, User, user_id)
    if not user.memory_enabled: raise HTTPException(409, 'Enable memory retention before adding preferences')
    row = Memory(user_id=user_id, content=payload.content, source='user_statement', confirmed=True)
    db.add(row)
    db.commit()
    return row

@app.post('/api/users/{user_id}/memories/{memory_id}/confirm', response_model=MemoryOut)
def confirm_memory(user_id: str, memory_id: str, db: Session = Depends(get_db)):
    user = require(db, User, user_id)
    if not user.memory_enabled: raise HTTPException(409, 'Memory retention is disabled')
    row = require(db, Memory, memory_id)
    if row.user_id != user_id: raise HTTPException(404, 'Memory not found')
    memory.confirm_memory(row)
    db.commit()
    return row

@app.delete('/api/users/{user_id}/memories/{memory_id}', response_model=Deleted)
def remove_memory(user_id: str, memory_id: str, db: Session = Depends(get_db)):
    row = require(db, Memory, memory_id)
    if row.user_id != user_id: raise HTTPException(404, 'Memory not found')
    memory.delete_memory(db, row)
    db.commit()
    return Deleted(deleted=True)

@app.patch('/api/users/{user_id}/memories/{memory_id}', response_model=MemoryOut)
def edit_memory(user_id: str, memory_id: str, payload: MemoryCreate, db: Session = Depends(get_db)):
    user = require(db, User, user_id)
    if not user.memory_enabled: raise HTTPException(409, 'Memory retention is disabled')
    row = require(db, Memory, memory_id)
    if row.user_id != user_id: raise HTTPException(404, 'Memory not found')
    row.content, row.source, row.confirmed, row.updated_at = payload.content, 'user_statement', True, now()
    db.commit()
    return row

@app.delete('/api/users/{user_id}/history', response_model=Deleted)
def remove_history(user_id: str, db: Session = Depends(get_db)):
    require(db, User, user_id)
    rows = list(db.scalars(select(Conversation).where(Conversation.user_id == user_id)))
    # Hold all distinct stripes to prevent turns/end/delete racing with deletion.
    indices = sorted({hash(r.id) % len(locks) for r in rows} | {hash(user_id) % len(locks)})
    acquired = []
    try:
        for i in indices:
            if not locks[i].acquire(blocking=False): raise HTTPException(409, 'Wait for active operations to finish before deleting history')
            acquired.append(i)
        memory.delete_user_history(db, user_id)
        db.commit()
    finally:
        for i in reversed(acquired): locks[i].release()
    return Deleted(deleted=True)

@app.post('/api/sessions', response_model=SessionDetail, status_code=201)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    with operation(payload.user_id):
        require(db, User, payload.user_id)
        row = memory.save_session(db, payload.user_id)
        reply = response(db, row)
        memory.save_message(db, row.id, 'assistant', reply.response)
        db.commit()
        return memory.session_detail(db, row)

@app.get('/api/sessions', response_model=list[SessionOut])
def sessions(user_id: str, db: Session = Depends(get_db)):
    require(db, User, user_id)
    return list(db.scalars(select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.started_at.desc())))

@app.get('/api/sessions/{session_id}', response_model=SessionDetail)
def session(session_id: str, db: Session = Depends(get_db)):
    return memory.session_detail(db, require(db, Conversation, session_id))

@app.post('/api/sessions/{session_id}/text-turns', response_model=TurnOut)
def text_turn(session_id: str, payload: TextTurn, db: Session = Depends(get_db)):
    with operation(session_id):
        row = require(db, Conversation, session_id)
        active(row)
        text = payload.text.strip()
        if not text: raise HTTPException(422, 'Please enter a response')
        evidence = perception.fusion.aggregate(Prediction(model='SpeechBrain', reason='Text-only turn'),
            Prediction(model='DeepFace', reason='Text-only turn'), Transcript(text=text))
        return commit_turn(db, row, evidence)

@app.post('/api/sessions/{session_id}/turns', response_model=TurnOut)
def media_turn(session_id: str, media: UploadFile = File(...), language: str | None = Form(None),
               consent: bool = Form(False), db: Session = Depends(get_db)):
    if not consent: raise HTTPException(422, 'Explicit recording consent is required')
    if language and not re.fullmatch('[a-z]{2,3}', language): raise HTTPException(422, 'Use a language code such as en, hi, or leave it blank')
    with operation(session_id):
        row = require(db, Conversation, session_id)
        active(row)
        try:
            with tempfile.TemporaryDirectory(prefix='affect-') as directory:
                folder = Path(directory)
                source = folder / 'recording'  # Ignore untrusted upload filename.
                size = 0
                with source.open('wb') as target:
                    while chunk := media.file.read(1024 * 1024):
                        size += len(chunk)
                        if size > settings.max_upload_mb * 1024 * 1024: raise HTTPException(413, 'Recording exceeds upload size limit')
                        target.write(chunk)
                evidence = perception.analyze(process_media(source, folder), language)
                return commit_turn(db, row, evidence)
        except MediaError as exc: raise HTTPException(422, str(exc)) from exc
        except PerceptionError as exc: raise HTTPException(503, str(exc)) from exc
        finally: media.file.close()

@app.post('/api/sessions/{session_id}/feedback', response_model=FeedbackOut)
def feedback(session_id: str, payload: FeedbackCreate, db: Session = Depends(get_db)):
    with operation(session_id):
        row = require(db, Observation, payload.observation_id)
        if row.session_id != session_id: raise HTTPException(404, 'Observation not found in session')
        if payload.choice == 'no' and not payload.user_reported_emotion:
            raise HTTPException(422, 'Describe your emotion for a correction')
        result = memory.save_feedback(db, payload)
        db.commit()
        return result

@app.post('/api/sessions/{session_id}/end', response_model=SessionDetail)
def end(session_id: str, db: Session = Depends(get_db)):
    with operation(session_id):
        row = require(db, Conversation, session_id)
        row.ended_at = row.ended_at or now()
        db.commit()
        return memory.session_detail(db, row)

@app.delete('/api/sessions/{session_id}', response_model=Deleted)
def delete_session(session_id: str, db: Session = Depends(get_db)):
    with operation(session_id):
        db.delete(require(db, Conversation, session_id))
        db.commit()
        return Deleted(deleted=True)

@app.get('/api/sessions/{session_id}/analytics', response_model=list[ObservationOut])
def analytics(session_id: str, db: Session = Depends(get_db)):
    return memory.session_detail(db, require(db, Conversation, session_id)).observations
