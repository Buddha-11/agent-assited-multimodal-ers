import logging
import numpy as np
import soundfile as sf
from .base import LazyModel
from ..config import settings
from ..schemas import Prediction

log = logging.getLogger(__name__)

class AudioEmotionModel(LazyModel):
    package = 'speechbrain'
    def load(self):
        import torch
        torch.set_num_threads(4)
        from speechbrain.inference.interfaces import foreign_class
        from speechbrain.utils.fetching import LocalStrategy
        device = settings.audio_device
        if device == 'auto': device = 'cuda' if torch.cuda.is_available() else 'cpu'
        if device == 'cuda' and not torch.cuda.is_available():
            log.warning('CUDA unavailable; using CPU for SpeechBrain')
            device = 'cpu'
        kwargs = dict(source=settings.audio_emotion_model, pymodule_file='custom_interface.py',
                      classname='CustomEncoderWav2vec2Classifier', savedir=settings.model_cache + '/speechbrain',
                      local_strategy=LocalStrategy.COPY, run_opts={'device': device})
        try: return foreign_class(**kwargs)
        except torch.cuda.OutOfMemoryError:
            log.warning('GPU memory exhausted during model loading; retrying on CPU')
            torch.cuda.empty_cache()
            kwargs['run_opts'] = {'device': 'cpu'}
            return foreign_class(**kwargs)
    def predict(self, wav):
        import torch
        signal, rate = sf.read(wav, dtype='float32')
        if rate != 16000 or signal.ndim != 1: raise ValueError('Expected mono 16 kHz WAV')
        if len(signal) < 8000 or float(np.sqrt(np.mean(signal ** 2))) < 0.001:
            return Prediction(model=settings.audio_emotion_model, reason='Audio too short or silent')
        classifier = self.get()
        classifier.hparams.label_encoder.expect_len(len(classifier.hparams.label_encoder.ind2lab))
        with torch.inference_mode():
            scores, _, _, labels = classifier.classify_batch(torch.from_numpy(signal).unsqueeze(0))
        values = scores.detach().cpu().reshape(-1).tolist()
        mapping = classifier.hparams.label_encoder.ind2lab
        if len(mapping) != len(values): raise ValueError('Checkpoint scores do not match label mapping')
        return Prediction(available=True, model=settings.audio_emotion_model, predicted_label=str(labels[0]),
                          scores={str(mapping[i]): float(v) for i, v in enumerate(values)})
