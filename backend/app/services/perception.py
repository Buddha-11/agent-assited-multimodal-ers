import logging
from typing import Protocol
from threading import BoundedSemaphore
import numpy as np
import soundfile as sf
from ..models.transcription import TranscriptionModel
from ..models.audio_emotion import AudioEmotionModel
from ..models.face_emotion import FaceEmotionModel
from ..schemas import Prediction, Transcript, Evidence
from .fusion import IndependentEvidenceFusion

log = logging.getLogger(__name__)
class PerceptionError(Exception): pass

class PerceptionPipeline(Protocol):
    def analyze(self, media, language: str | None = None) -> Evidence: ...

class StandardPerception:
    def __init__(self):
        self.whisper, self.audio, self.face = TranscriptionModel(), AudioEmotionModel(), FaceEmotionModel()
        self.capacity = BoundedSemaphore(1)
        self.fusion = IndependentEvidenceFusion()
    def status(self):
        return {'whisper': self.whisper.status(), 'speechbrain': self.audio.status(), 'deepface': self.face.status()}
    def analyze(self, media, language=None):
        if not self.capacity.acquire(blocking=False): raise PerceptionError('Another recording is processing. Try again shortly.')
        try:
            transcript = Transcript()
            audio = Prediction(model='speechbrain/emotion-recognition-wav2vec2-IEMOCAP', reason='No audio stream')
            if media.wav:
                signal, rate = sf.read(media.wav)
                duration = len(signal) / rate
                if duration < 0.5:
                    raise PerceptionError('Recording is too short. Speak for at least one second before stopping, or type a response.')
                if float(np.sqrt(np.mean(signal ** 2))) < 0.001:
                    raise PerceptionError('Recording is silent or too quiet. Check the Microphone check bars, select the correct input, and check your microphone mute switch or input volume before recording again.')
                try: transcript = self.whisper.predict(media.wav, language)
                except Exception as exc:
                    self.whisper.inference_failed()
                    log.exception('Transcription failed')
                    raise PerceptionError('Transcription unavailable. Check model diagnostics or type a response.') from exc
                self.whisper.inference_succeeded()
                try:
                    audio = self.audio.predict(media.wav)
                    self.audio.inference_succeeded()
                except Exception:
                    self.audio.inference_failed()
                    log.exception('Audio emotion inference failed')
                    audio.reason = 'Audio emotion inference unavailable; check model diagnostics'
            try:
                visual = self.face.predict(media.frames)
                if media.frames: self.face.inference_succeeded()
            except Exception:
                self.face.inference_failed()
                log.exception('Facial expression inference failed')
                visual = Prediction(model='DeepFace/Emotion', reason='Facial inference unavailable; check model diagnostics')
            if not transcript.text: raise PerceptionError('No speech detected. Please record again or type a response.')
            return self.fusion.aggregate(audio, visual, transcript)
        finally: self.capacity.release()

perception = StandardPerception()
