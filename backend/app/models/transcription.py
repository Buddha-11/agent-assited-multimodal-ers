from .base import LazyModel
from ..config import settings
from ..schemas import Transcript

class TranscriptionModel(LazyModel):
    package = 'faster_whisper'
    def load(self):
        from faster_whisper import WhisperModel
        device = settings.whisper_device
        if device == 'auto':
            import ctranslate2
            device = 'cuda' if ctranslate2.get_cuda_device_count() else 'cpu'
        return WhisperModel(settings.whisper_model, device=device,
                           compute_type=settings.whisper_compute_type,
                           download_root=settings.model_cache + '/whisper')
    def predict(self, wav, language=None):
        segments, info = self.get().transcribe(str(wav), language=language, vad_filter=True,
            condition_on_previous_text=False, no_speech_threshold=0.6)
        valid = [s for s in segments if s.no_speech_prob < 0.6 and s.avg_logprob > -1.0]
        return Transcript(text=' '.join(s.text.strip() for s in valid).strip(), language=info.language,
                          segments=[{'start': s.start, 'end': s.end, 'text': s.text.strip()} for s in valid])
