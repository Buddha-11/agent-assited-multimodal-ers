import numpy as np
import soundfile as sf
import pytest
from backend.app.services.media import command,process_media,MediaError
from backend.app.models.face_emotion import FaceEmotionModel
from backend.app.models.audio_emotion import AudioEmotionModel
from backend.app.services.perception import StandardPerception,PerceptionError
from backend.app.config import settings

def test_audio_extraction_and_missing_video(tmp_path):
    source=tmp_path/'input.wav'
    sf.write(source,np.sin(np.arange(32000)*.1)*.2,32000)
    media=process_media(source,tmp_path)
    audio,rate=sf.read(media.wav)
    assert rate==16000 and audio.ndim==1 and len(audio)>=15000
    assert media.frames==[]

def test_missing_audio(tmp_path):
    source=tmp_path/'video.webm'
    result=command(['-y','-f','lavfi','-i','color=c=black:s=160x120:d=1','-c:v','libvpx',str(source)])
    assert result.returncode==0
    media=process_media(source,tmp_path)
    assert media.wav is None and len(media.frames)>0

def test_duration_limit(tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'max_recording_seconds',1)
    source=tmp_path/'long.wav'
    sf.write(source,np.zeros(32000),16000)
    with pytest.raises(MediaError,match='duration'): process_media(source,tmp_path)

def test_no_face_does_not_make_predictions(monkeypatch):
    class NoFace:
        @staticmethod
        def analyze(*args,**kwargs):
            assert kwargs['enforce_detection'] is True
            raise ValueError('Face could not be detected')
    model=FaceEmotionModel()
    monkeypatch.setattr(model,'get',lambda:NoFace)
    result=model.predict(['frame.jpg'])
    assert not result.available and result.frames_with_faces==0 and result.scores=={}

def test_ambiguous_faces(monkeypatch):
    class MultiFace:
        @staticmethod
        def analyze(*args,**kwargs): return [{},{}]
    model=FaceEmotionModel()
    monkeypatch.setattr(model,'get',lambda:MultiFace)
    result=model.predict(['frame.jpg'])
    assert not result.available and result.ambiguous_frames==1

def test_silence(tmp_path):
    source=tmp_path/'silent.wav'
    sf.write(source,np.zeros(16000),16000)
    assert not AudioEmotionModel().predict(source).available
    from backend.app.services.media import ProcessedMedia
    with pytest.raises(PerceptionError,match='silent'): StandardPerception().analyze(ProcessedMedia(source,[],1))

def test_short_recording_has_specific_guidance(tmp_path):
    from backend.app.services.media import ProcessedMedia
    source=tmp_path/'short.wav'
    sf.write(source,np.ones(1600)*.05,16000)
    with pytest.raises(PerceptionError,match='at least one second'):
        StandardPerception().analyze(ProcessedMedia(source,[],.1))

def test_optional_modality_failure(monkeypatch):
    from backend.app.services.media import ProcessedMedia
    from backend.app.schemas import Transcript
    model=StandardPerception()
    monkeypatch.setattr('backend.app.services.perception.sf.read',lambda path:(np.ones(16000)*.1,16000))
    monkeypatch.setattr(model.whisper,'predict',lambda *args:Transcript(text='I finished my work.'))
    def fail(*args):raise RuntimeError('Model failed')
    monkeypatch.setattr(model.audio,'predict',fail)
    monkeypatch.setattr(model.face,'predict',fail)
    result=model.analyze(ProcessedMedia('audio.wav',['face.jpg'],1))
    assert result.transcript.text and result.agreement=='unavailable' and result.audio.scores=={}
