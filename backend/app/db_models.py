from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc).isoformat()

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(default='Research participant')
    created_at: Mapped[str] = mapped_column(default=now)
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class Conversation(Base):
    __tablename__ = 'sessions'
    id: Mapped[str] = mapped_column(primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    started_at: Mapped[str] = mapped_column(default=now)
    ended_at: Mapped[str | None]
    summary: Mapped[str | None]

class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[str] = mapped_column(primary_key=True, default=uid)
    session_id: Mapped[str] = mapped_column(ForeignKey('sessions.id', ondelete='CASCADE'), index=True)
    role: Mapped[str]
    text: Mapped[str]
    timestamp: Mapped[str] = mapped_column(default=now)

class Observation(Base):
    __tablename__ = 'emotion_observations'
    id: Mapped[str] = mapped_column(primary_key=True, default=uid)
    session_id: Mapped[str] = mapped_column(ForeignKey('sessions.id', ondelete='CASCADE'), index=True)
    message_id: Mapped[str] = mapped_column(ForeignKey('messages.id', ondelete='CASCADE'), unique=True)
    audio_prediction_json: Mapped[dict] = mapped_column(JSON)
    visual_prediction_json: Mapped[dict] = mapped_column(JSON)
    interpretation_json: Mapped[dict] = mapped_column(JSON)
    timestamp: Mapped[str] = mapped_column(default=now)

class Feedback(Base):
    __tablename__ = 'emotion_feedback'
    id: Mapped[str] = mapped_column(primary_key=True, default=uid)
    observation_id: Mapped[str] = mapped_column(ForeignKey('emotion_observations.id', ondelete='CASCADE'), unique=True)
    choice: Mapped[str]
    user_reported_emotion: Mapped[str | None]
    optional_comment: Mapped[str | None]
    timestamp: Mapped[str] = mapped_column(default=now)

class Memory(Base):
    __tablename__ = 'user_memories'
    id: Mapped[str] = mapped_column(primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    content: Mapped[str]
    source: Mapped[str]
    confirmed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[str] = mapped_column(default=now)
    updated_at: Mapped[str] = mapped_column(default=now)
