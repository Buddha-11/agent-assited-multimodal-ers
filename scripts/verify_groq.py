"""Real text conversation smoke test; no mocks and no printed credentials."""
import json
import sys
import argparse
import httpx
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings

report = {'provider': 'Groq', 'model': settings.llm_model, 'mocked': False, 'results': [], 'errors': []}
parser = argparse.ArgumentParser()
parser.add_argument('--base-url', help='Use the running backend or frontend API proxy instead of TestClient')
args = parser.parse_args()
report['api_transport'] = args.base_url or 'FastAPI TestClient (real Groq provider)'
with (httpx.Client(base_url=args.base_url, timeout=90) if args.base_url else TestClient(app)) as client:
    user = client.post('/api/users', json={'name': 'Disposable provider smoke test'}).json()
    try:
        opening = client.post('/api/sessions', json={'user_id': user['id']})
        if opening.status_code != 201:
            report['errors'].append({'step': 'opening', 'status': opening.status_code, 'detail': opening.json()})
        else:
            session = opening.json()
            report['results'].append({'step': 'opening', 'status': 201, 'response': session['messages'][0]['text']})
            for text in ['I spent all evening debugging my university project.', 'Actually, I finally fixed it! Please give me one practical next step.']:
                turn = client.post(f"/api/sessions/{session['id']}/text-turns", json={'text': text})
                if turn.status_code != 200:
                    report['errors'].append({'step': 'text_turn', 'status': turn.status_code, 'detail': turn.json()})
                    break
                data = turn.json()
                reply = data['agent']
                if reply['reason'] == 'Provider output did not match the response schema.':
                    report['errors'].append({'step': 'structured_response', 'detail': 'Invalid provider output used the explicit formatting fallback'})
                report['results'].append({'step': 'text_turn', 'status': 200, 'input': text, 'agent': reply,
                    'message_count': len(data['session']['messages']),
                    'modality_agreement': data['session']['observations'][-1]['evidence']['agreement']})
    finally:
        cleanup = client.delete(f"/api/users/{user['id']}/history")
        report['test_history_deleted'] = cleanup.status_code == 200

output = ROOT / 'output/verification/groq-conversation-smoke.json'
output.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
sys.exit(1 if report['errors'] else 0)
