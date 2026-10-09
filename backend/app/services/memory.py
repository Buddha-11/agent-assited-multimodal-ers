from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from ..db_models import User, Conversation, Message, Observation, Feedback, Memory, now
from ..schemas import SessionDetail, ObservationOut, Evidence, Profile

def get_recent_history(db: Session, session_id: str):
    rows = list(db.scalars(select(Message).where(Message.session_id == session_id).order_by(Message.timestamp.desc()).limit(16)))
    return [{'role': m.role, 'content': m.text} for m in reversed(rows)]

def get_relevant_memories(db: Session, user: User):
    if not user.memory_enabled: return []
    return list(db.scalars(select(Memory).where(Memory.user_id == user.id, Memory.confirmed == True).order_by(Memory.updated_at.desc()).limit(12)))

def recent_feedback(db: Session, user_id: str, session_id: str | None = None):
    query = select(Feedback).join(Observation, Feedback.observation_id == Observation.id)
    query = query.join(Conversation, Observation.session_id == Conversation.id).where(Conversation.user_id == user_id)
    if session_id: query = query.where(Conversation.id == session_id)
    rows = db.scalars(query.order_by(Feedback.timestamp.desc()).limit(8))
    return [{'choice': f.choice, 'user_reported_emotion': f.user_reported_emotion,
             'comment': f.optional_comment} for f in rows]

def propose_memory(db: Session, user: User, content: str | None):
    if not content or not user.memory_enabled: return None
    if db.scalar(select(Memory).where(Memory.user_id == user.id, Memory.content == content)): return None
    memory = Memory(user_id=user.id, content=content, source='agent_proposal', confirmed=False)
    db.add(memory)
    db.flush()
    return memory

def confirm_memory(memory: Memory):
    memory.confirmed, memory.updated_at = True, now()

def save_session(db: Session, user_id: str):
    row = Conversation(user_id=user_id)
    db.add(row)
    db.flush()
    return row

def save_message(db: Session, session_id: str, role: str, text: str):
    row = Message(session_id=session_id, role=role, text=text)
    db.add(row)
    db.flush()
    return row

def save_emotion_observation(db: Session, session_id: str, message_id: str, evidence: Evidence):
    row = Observation(session_id=session_id, message_id=message_id,
        audio_prediction_json=evidence.audio.model_dump(), visual_prediction_json=evidence.visual.model_dump(),
        interpretation_json=evidence.model_dump())
    db.add(row)
    db.flush()
    return row

def save_feedback(db: Session, payload):
    row = db.scalar(select(Feedback).where(Feedback.observation_id == payload.observation_id))
    if not row:
        row = Feedback(observation_id=payload.observation_id)
        db.add(row)
    for key, value in payload.model_dump(exclude={'observation_id'}).items(): setattr(row, key, value)
    row.timestamp = now()
    db.flush()
    return row

def session_detail(db: Session, row: Conversation):
    observations = list(db.scalars(select(Observation).where(Observation.session_id == row.id).order_by(Observation.timestamp)))
    feedback = {f.observation_id: f for f in db.scalars(select(Feedback).where(Feedback.observation_id.in_([o.id for o in observations])))}
    return SessionDetail(id=row.id, user_id=row.user_id, started_at=row.started_at, ended_at=row.ended_at,
        summary=row.summary, messages=list(db.scalars(select(Message).where(Message.session_id == row.id).order_by(Message.timestamp))),
        observations=[ObservationOut(id=o.id, message_id=o.message_id, timestamp=o.timestamp,
                        evidence=Evidence.model_validate(o.interpretation_json), feedback=feedback.get(o.id)) for o in observations])

def get_user_profile(db: Session, user: User):
    return Profile(user=user, session_count=db.scalar(select(func.count()).select_from(Conversation).where(Conversation.user_id == user.id)),
        memories=list(db.scalars(select(Memory).where(Memory.user_id == user.id).order_by(Memory.created_at.desc()))),
        recent_sessions=list(db.scalars(select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.started_at.desc()).limit(8))),
        feedback=list(db.scalars(select(Feedback).join(Observation, Feedback.observation_id == Observation.id)
            .join(Conversation, Observation.session_id == Conversation.id).where(Conversation.user_id == user.id)
            .order_by(Feedback.timestamp.desc()).limit(20))))

def delete_memory(db: Session, memory: Memory): db.delete(memory)
def delete_user_history(db: Session, user_id: str):
    db.execute(delete(Conversation).where(Conversation.user_id == user_id))
    db.execute(delete(Memory).where(Memory.user_id == user_id))
