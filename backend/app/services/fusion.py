from typing import Protocol
from ..schemas import Evidence, Prediction, Transcript

class FusionStrategy(Protocol):
    def aggregate(self, audio: Prediction, visual: Prediction, transcript: Transcript) -> Evidence: ...

COMMON = {'ang': 'anger', 'angry': 'anger', 'hap': 'happiness', 'happy': 'happiness',
          'sad': 'sadness', 'neu': 'neutral', 'neutral': 'neutral'}

class IndependentEvidenceFusion:
    def aggregate(self, audio: Prediction, visual: Prediction, transcript: Transcript) -> Evidence:
        a = COMMON.get(audio.predicted_label or '', audio.predicted_label)
        v = COMMON.get(visual.predicted_label or '', visual.predicted_label)
        if audio.available and visual.available:
            agreement = 'agree' if a == v else 'disagree'
            interpretation = a if agreement == 'agree' else 'mixed_signals'
        elif audio.available or visual.available:
            agreement, interpretation = 'single_modality', a if audio.available else v
        else:
            agreement, interpretation = 'unavailable', 'unknown'
        return Evidence(audio=audio, visual=visual, transcript=transcript,
                        agreement=agreement, interpretation=interpretation or 'unknown', uncertain=True)
