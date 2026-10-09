from backend.app.schemas import Prediction, Transcript
from backend.app.services.fusion import IndependentEvidenceFusion
from backend.app.agent.conversation_agent import AgentUnavailable, OpenAICompatibleProvider
from backend.app.config import settings

def test_health(client):
    result = client.get('/api/health')
    assert result.status_code == 200
    assert set(result.json()['models']) == {'llm','whisper','speechbrain','deepface','ffmpeg'}
    assert client.get('/api/settings').status_code == 200
    assert 'api_key' not in client.get('/api/settings').text

def test_text_history_end_and_delete(client, session):
    user, row = session
    result = client.post(f"/api/sessions/{row['id']}/text-turns", json={'text':'I fixed my project.'})
    assert result.status_code == 200
    detail = result.json()['session']
    assert len(detail['messages']) == 3
    evidence = detail['observations'][0]['evidence']
    assert evidence['agreement'] == 'unavailable'
    assert evidence['audio']['scores'] == {}
    assert evidence['visual']['scores'] == {}
    assert client.get(f"/api/sessions/{row['id']}/analytics").json()[0]['id']
    assert client.post(f"/api/sessions/{row['id']}/end").status_code == 200
    assert client.post(f"/api/sessions/{row['id']}/text-turns", json={'text':'Hi'}).status_code == 409
    assert client.delete(f"/api/sessions/{row['id']}").status_code == 200
    assert client.get(f"/api/sessions/{row['id']}").status_code == 404
    assert client.get('/api/sessions',params={'user_id':user['id']}).json() == []

def test_feedback_update_and_memory(client,session):
    user,row = session
    turn = client.post(f"/api/sessions/{row['id']}/text-turns",json={'text':'A quiet day'}).json()
    observation = turn['session']['observations'][0]
    payload={'observation_id':observation['id'],'choice':'no','user_reported_emotion':'content','optional_comment':'My voice is naturally quiet.'}
    first=client.post(f"/api/sessions/{row['id']}/feedback",json=payload)
    assert first.status_code == 200
    payload['user_reported_emotion']='relaxed'
    second=client.post(f"/api/sessions/{row['id']}/feedback",json=payload)
    assert first.json()['id']==second.json()['id']
    path=f"/api/users/{user['id']}"
    mem=client.post(path+'/memories',json={'content':'I prefer practical suggestions.'})
    assert mem.status_code == 201 and mem.json()['confirmed']
    edited=client.patch(path+f"/memories/{mem.json()['id']}",json={'content':'I prefer short practical suggestions.'})
    assert edited.status_code==200 and edited.json()['confirmed']
    assert edited.json()['content']=='I prefer short practical suggestions.'
    next_session=client.post('/api/sessions',json={'user_id':user['id']}).json()
    assert next_session['messages'][0]['text']=='I will keep suggestions practical.'
    assert client.patch(path+'/profile',json={'memory_enabled':False}).status_code == 200
    assert client.post(path+'/memories',json={'content':'New preference'}).status_code == 409
    disabled_session=client.post('/api/sessions',json={'user_id':user['id']}).json()
    assert disabled_session['messages'][0]['text']=='Tell me more about your project.'
    assert client.delete(path+'/history').status_code == 200
    profile=client.get(path+'/profile').json()
    assert profile['session_count']==0 and profile['memories']==[] and profile['feedback']==[]

def test_memory_candidate_requires_confirmation(client,session,monkeypatch):
    from backend.app.main import agent
    from backend.app.schemas import AgentReply
    user,row=session
    seen=[]
    def reply(history,evidence,memories,feedback):
        seen.append(memories)
        return AgentReply(response='I can remember that if you confirm.',strategy='answer',reason='Acknowledge preference.',memory_candidate='Prefers concise replies.')
    monkeypatch.setattr(agent,'respond',reply)
    turn=client.post(f"/api/sessions/{row['id']}/text-turns",json={'text':'I prefer concise replies.'}).json()
    candidate=turn['memory_candidate']
    assert candidate and not candidate['confirmed']
    client.post('/api/sessions',json={'user_id':user['id']})
    assert seen[-1]==[]
    assert client.post(f"/api/users/{user['id']}/memories/{candidate['id']}/confirm").status_code==200
    client.post('/api/sessions',json={'user_id':user['id']})
    assert seen[-1]==['Prefers concise replies.']

def test_llm_failure_rolls_back(client,session,monkeypatch):
    from backend.app.main import agent
    def fail(*args): raise AgentUnavailable('Provider unavailable')
    monkeypatch.setattr(agent,'respond',fail)
    user,row=session
    result=client.post(f"/api/sessions/{row['id']}/text-turns",json={'text':'Hi'})
    assert result.status_code == 503
    assert len(client.get(f"/api/sessions/{row['id']}").json()['messages']) == 1
    assert client.post('/api/sessions',json={'user_id':user['id']}).status_code == 503
    assert len(client.get('/api/sessions',params={'user_id':user['id']}).json()) == 1

def test_unconfigured_provider(monkeypatch):
    import pytest
    monkeypatch.setattr(settings,'llm_model','')
    with pytest.raises(AgentUnavailable): OpenAICompatibleProvider().complete([])

def test_invalid_upload_and_consent(client,session):
    _,row=session
    path=f"/api/sessions/{row['id']}/turns"
    assert client.post(path,files={'media':('../../bad.webm',b'not media','video/webm')}).status_code == 422
    result=client.post(path,data={'consent':'true'},files={'media':('../../bad.webm',b'not media','video/webm')})
    assert result.status_code==422
    assert client.post(f"/api/sessions/{row['id']}/text-turns",json={'text':'   '}).status_code == 422

def test_session_overlap(client,session):
    from backend.app.main import operation
    _,row=session
    with operation(row['id']):
        assert client.post(f"/api/sessions/{row['id']}/text-turns",json={'text':'Hi'}).status_code==409
        assert client.delete(f"/api/sessions/{row['id']}").status_code==409
        assert client.post(f"/api/sessions/{row['id']}/end").status_code==409

def test_fusion():
    fusion=IndependentEvidenceFusion()
    audio=Prediction(available=True,model='SpeechBrain',predicted_label='sad',scores={'sad':.8})
    face=Prediction(available=True,model='DeepFace',predicted_label='neutral',scores={'neutral':.7})
    evidence=fusion.aggregate(audio,face,Transcript(text='Today was long.'))
    assert evidence.interpretation=='mixed_signals' and evidence.uncertain
    assert evidence.audio.scores=={'sad':.8}
    assert fusion.aggregate(audio,Prediction(model='DeepFace'),Transcript()).agreement=='single_modality'
    audio.predicted_label='neu'
    assert fusion.aggregate(audio,face,Transcript()).agreement=='agree'
