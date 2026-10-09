from pathlib import Path
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / 'backend/.env', override=False)
os.environ.setdefault('HF_HOME', str(ROOT / '.cache/huggingface'))
os.environ.setdefault('DEEPFACE_HOME', str(ROOT / '.cache'))
os.environ.setdefault('USE_TF', '0')  # Transformers' PyTorch models do not need TensorFlow.

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / 'backend/.env', extra='ignore')
    llm_api_key: str = ''
    llm_base_url: str = 'https://api.openai.com/v1'
    llm_model: str = ''
    llm_temperature: float = Field(0.7, ge=0, le=2)
    llm_max_output_tokens: int = Field(400, ge=32, le=4096)
    llm_timeout: float = Field(45, gt=0)
    llm_require_api_key: bool = True
    llm_response_format: Literal['json_object', 'json_schema'] = 'json_object'
    llm_reasoning_effort: Literal['low', 'medium', 'high'] | None = None
    whisper_model: str = 'base'
    whisper_device: str = 'cpu'
    whisper_compute_type: str = 'int8'
    audio_emotion_model: str = 'speechbrain/emotion-recognition-wav2vec2-IEMOCAP'
    audio_device: str = 'auto'
    face_frame_interval: float = Field(1, ge=0.25, le=30)
    database_url: str = 'sqlite:///./data/emotion_agent.db'
    max_recording_seconds: int = Field(30, ge=1, le=120)
    max_upload_mb: int = Field(25, ge=1, le=100)
    cors_origins: list[str] = ['http://localhost:5173', 'http://127.0.0.1:5173']
    ffmpeg_path: str = ''
    model_cache: str = str(ROOT / '.cache/models')

settings = Settings()
