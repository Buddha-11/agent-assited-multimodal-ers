import httpx
import pytest
from backend.app.agent.conversation_agent import OpenAICompatibleProvider,AgentUnavailable
from backend.app.config import settings

def provider(monkeypatch,response):
    monkeypatch.setattr(settings,'llm_model','test-model')
    monkeypatch.setattr(settings,'llm_api_key','test-only')
    original=httpx.Client
    transport=httpx.MockTransport(lambda request:response)
    monkeypatch.setattr(httpx,'Client',lambda **kwargs:original(transport=transport,**kwargs))
    return OpenAICompatibleProvider()

def test_structured_llm_response(monkeypatch):
    response=httpx.Response(200,json={'choices':[{'message':{'content':'{"response":"What did you fix?","strategy":"explore","reason":"Follow the project topic.","memory_candidate":null}'}}]})
    model=provider(monkeypatch,response)
    assert model.complete([{'role':'user','content':'I fixed my project.'}]).strategy=='explore'
    assert model.status().state=='ready'

def test_invalid_structured_llm_response(monkeypatch):
    response=httpx.Response(200,json={'choices':[{'message':{'content':'Not JSON'}}]})
    result=provider(monkeypatch,response).complete([])
    assert result.strategy=='clarify' and result.memory_candidate is None

def test_llm_http_failure(monkeypatch):
    model=provider(monkeypatch,httpx.Response(401,json={'error':'Invalid credential'}))
    with pytest.raises(AgentUnavailable):model.complete([])
    assert model.status().state=='failed'

def test_groq_request_uses_strict_schema_without_reasoning(monkeypatch):
    import json
    monkeypatch.setattr(settings,'llm_model','openai/gpt-oss-20b')
    monkeypatch.setattr(settings,'llm_base_url','https://api.groq.com/openai/v1')
    monkeypatch.setattr(settings,'llm_api_key','test-only')
    monkeypatch.setattr(settings,'llm_response_format','json_schema')
    monkeypatch.setattr(settings,'llm_reasoning_effort','low')
    captured=[]
    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps({'response':'What did you fix?','strategy':'explore','reason':'Follow the topic.','memory_candidate':None}), 'reasoning':'This field must never be returned by the app.'}}]})
    original=httpx.Client
    monkeypatch.setattr(httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs))
    result=OpenAICompatibleProvider().complete([])
    payload=captured[0]
    assert payload['include_reasoning'] is False and payload['reasoning_effort']=='low'
    assert 'max_completion_tokens' in payload and 'max_tokens' not in payload
    schema=payload['response_format']['json_schema']
    assert schema['strict'] and schema['schema']['additionalProperties'] is False
    assert 'memory_candidate' in schema['schema']['required']
    assert 'reasoning' not in result.model_dump()

def test_rate_limit_diagnostic(monkeypatch):
    model=provider(monkeypatch,httpx.Response(429,json={'error':'Rate limit'}))
    with pytest.raises(AgentUnavailable,match='rate limit'):model.complete([])
