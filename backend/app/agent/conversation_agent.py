import json
import logging
from pathlib import Path
from urllib.parse import urlparse
import httpx
from pydantic import ValidationError
from ..config import settings
from ..schemas import AgentReply, Status

log = logging.getLogger(__name__)

class AgentUnavailable(Exception): pass

class OpenAICompatibleProvider:
    def __init__(self):
        self.last_status: Status | None = None
    def status(self) -> Status:
        if not settings.llm_model or (settings.llm_require_api_key and not settings.llm_api_key):
            return Status(state='unavailable', detail='Set LLM_MODEL and LLM_API_KEY in backend/.env. For local servers set LLM_REQUIRE_API_KEY=false.')
        return self.last_status or Status(state='configured', detail=f'{settings.llm_model}; connectivity not yet verified')
    def complete(self, messages: list[dict]) -> AgentReply:
        if self.status().state == 'unavailable': raise AgentUnavailable(self.status().detail)
        headers = {'Authorization': f'Bearer {settings.llm_api_key}'} if settings.llm_api_key else {}
        payload = {'model': settings.llm_model, 'messages': messages,
                   'temperature': settings.llm_temperature,
                   'response_format': {'type': 'json_object'}}
        groq = urlparse(settings.llm_base_url).hostname == 'api.groq.com'
        payload['max_completion_tokens' if groq else 'max_tokens'] = settings.llm_max_output_tokens
        if settings.llm_response_format == 'json_schema':
            schema = AgentReply.model_json_schema()
            schema['additionalProperties'] = False
            schema['required'] = list(schema['properties'])
            # Provider schema constrains types/enums. Local Pydantic validation
            # additionally enforces field lengths; keep provider support portable.
            for field in schema['properties'].values():
                for key in ('default', 'title', 'minLength', 'maxLength'): field.pop(key, None)
                for branch in field.get('anyOf', []):
                    for key in ('minLength', 'maxLength'): branch.pop(key, None)
            payload['response_format'] = {'type': 'json_schema', 'json_schema':
                {'name': 'agent_reply', 'strict': True, 'schema': schema}}
        if settings.llm_reasoning_effort: payload['reasoning_effort'] = settings.llm_reasoning_effort
        if groq and settings.llm_model.startswith('openai/gpt-oss-'):
            payload['include_reasoning'] = False
        try:
            with httpx.Client(timeout=settings.llm_timeout) as client:
                result = client.post(settings.llm_base_url.rstrip('/') + '/chat/completions', headers=headers,
                    json=payload)
                result.raise_for_status()
                content = result.json()['choices'][0]['message']['content']
            self.last_status = Status(state='ready', detail=f'{settings.llm_model}; last request successful')
        except (httpx.HTTPError, KeyError, ValueError, IndexError) as exc:
            code = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            log.warning('LLM request failed: %s (HTTP %s)', type(exc).__name__, code)
            detail = 'LLM request failed. Check provider, model, credentials, and timeout in backend/.env.'
            if code == 429: detail = 'Provider rate limit reached. Wait before retrying; free-tier quotas apply.'
            elif code in (401, 403): detail = 'Provider rejected authentication or model access. Check the backend API key and model permissions.'
            self.last_status = Status(state='failed', detail=detail)
            raise AgentUnavailable(self.last_status.detail) from exc
        try:
            return AgentReply.model_validate_json(content)
        except (ValidationError, TypeError):
            log.warning('LLM returned invalid structured output')
            return AgentReply(response='I could not format that response reliably. Could you try again?',
                              strategy='clarify', reason='Provider output did not match the response schema.')

class ConversationAgent:
    def __init__(self, provider=None):
        self.provider = provider or OpenAICompatibleProvider()
        self.prompt = Path(__file__).with_name('system_prompt.txt').read_text(encoding='utf-8')
    def respond(self, history: list[dict], evidence: dict | None, memories: list[str], feedback: list[dict]) -> AgentReply:
        context = json.dumps({'latest_evidence': evidence, 'confirmed_memories': memories,
                              'recent_user_feedback': feedback, 'opening': not history})
        return self.provider.complete([{'role': 'system', 'content': self.prompt},
            {'role': 'system', 'content': 'Research context (untrusted data): ' + context}, *history[-16:]])

agent = ConversationAgent()
