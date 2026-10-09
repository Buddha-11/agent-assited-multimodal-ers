from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class UserCreate(BaseModel):
    name: str = Field('Research participant', min_length=1, max_length=100)
class ProfileUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    memory_enabled: bool | None = None
class SessionCreate(BaseModel):
    user_id: str
class TextTurn(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
class MemoryCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
class FeedbackCreate(BaseModel):
    observation_id: str
    choice: Literal['yes', 'no', 'unsure', 'decline']
    user_reported_emotion: str | None = Field(None, max_length=200)
    optional_comment: str | None = Field(None, max_length=1000)
class Prediction(BaseModel):
    available: bool = False
    model: str
    predicted_label: str | None = None
    scores: dict[str, float] = Field(default_factory=dict)
    score_kind: str = 'model_scores_not_calibrated'
    reason: str | None = None
    frames_processed: int = 0
    frames_with_faces: int = 0
    ambiguous_frames: int = 0
class Transcript(BaseModel):
    text: str = ''
    language: str | None = None
    segments: list[dict] = Field(default_factory=list)
class Evidence(BaseModel):
    audio: Prediction
    visual: Prediction
    transcript: Transcript
    agreement: Literal['agree', 'disagree', 'single_modality', 'unavailable']
    interpretation: str
    uncertain: bool = True
class AgentReply(BaseModel):
    response: str = Field(min_length=1, max_length=6000)
    strategy: Literal['explore', 'clarify', 'support', 'answer', 'change_topic', 'close_conversation']
    reason: str = Field(max_length=300)
    memory_candidate: str | None = Field(None, max_length=1000)
class Record(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
class UserOut(Record):
    name: str
    created_at: str
    memory_enabled: bool
class MemoryOut(Record):
    content: str
    source: str
    confirmed: bool
    created_at: str
    updated_at: str
class SessionOut(Record):
    user_id: str
    started_at: str
    ended_at: str | None
    summary: str | None
class MessageOut(Record):
    role: str
    text: str
    timestamp: str
class FeedbackOut(Record):
    choice: str
    user_reported_emotion: str | None
    optional_comment: str | None
    timestamp: str
class ObservationOut(Record):
    message_id: str
    timestamp: str
    evidence: Evidence
    feedback: FeedbackOut | None = None
class SessionDetail(SessionOut):
    messages: list[MessageOut]
    observations: list[ObservationOut]
class Profile(BaseModel):
    user: UserOut
    session_count: int
    memories: list[MemoryOut]
    recent_sessions: list[SessionOut]
    feedback: list[FeedbackOut]
class TurnOut(BaseModel):
    session: SessionDetail
    agent: AgentReply
    memory_candidate: MemoryOut | None = None
class Status(BaseModel):
    state: Literal['configured', 'loading', 'ready', 'unavailable', 'failed']
    detail: str
class Health(BaseModel):
    status: str
    max_recording_seconds: int
    models: dict[str, Status]
class Deleted(BaseModel):
    deleted: bool
class RuntimeSettings(BaseModel):
    model: str = Field(max_length=200)
    temperature: float = Field(ge=0, le=2)
    max_output_tokens: int = Field(ge=32, le=4096)
    timeout: float = Field(gt=0, le=300)
