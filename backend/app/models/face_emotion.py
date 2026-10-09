import logging
from .base import LazyModel
from ..schemas import Prediction

log = logging.getLogger(__name__)

class FaceEmotionModel(LazyModel):
    package = 'deepface'
    def load(self):
        import tensorflow as tf
        tf.config.set_visible_devices([], 'GPU')
        from deepface import DeepFace
        DeepFace.build_model('Emotion', task='facial_attribute')
        return DeepFace
    def predict(self, frames):
        if not frames: return Prediction(model='DeepFace/Emotion', reason='No video stream')
        detector = self.get()
        valid, ambiguous = [], 0
        for frame in frames:
            try:
                results = detector.analyze(str(frame), actions=['emotion'], detector_backend='opencv',
                                           enforce_detection=True, silent=True)
                if len(results) != 1:
                    ambiguous += 1
                    continue
                valid.append({str(k): float(v) / 100 for k, v in results[0]['emotion'].items()})
            except ValueError as exc:
                if 'Face could not be detected' not in str(exc): raise
                log.info('No face detected in sampled frame')
        if not valid:
            return Prediction(model='DeepFace/Emotion', reason='No unambiguous face detected',
                              frames_processed=len(frames), ambiguous_frames=ambiguous)
        scores = {k: sum(row[k] for row in valid) / len(valid) for k in valid[0]}
        return Prediction(available=True, model='DeepFace/Emotion', scores=scores,
            predicted_label=max(scores, key=scores.get), frames_processed=len(frames),
            frames_with_faces=len(valid), ambiguous_frames=ambiguous)
