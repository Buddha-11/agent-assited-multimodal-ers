import os
import sys
import tempfile
import atexit
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
test_dir = tempfile.TemporaryDirectory(prefix='affect-tests-')
os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(test_dir.name) / 'test.db').replace('\\', '/')

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, agent
from backend.app.database import Base, engine
from backend.app.schemas import AgentReply

@atexit.register
def cleanup_database():
    engine.dispose()
    test_dir.cleanup()

@pytest.fixture
def client(monkeypatch):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    def respond(history, evidence, memories, feedback):
        return AgentReply(response='Tell me more about your project.' if not memories else 'I will keep suggestions practical.',
            strategy='explore', reason='Follow the latest topic.', memory_candidate=None)
    monkeypatch.setattr(agent, 'respond', respond)
    with TestClient(app) as client: yield client

@pytest.fixture
def session(client):
    user = client.post('/api/users', json={'name':'Tester'}).json()
    conversation = client.post('/api/sessions', json={'user_id':user['id']})
    assert conversation.status_code == 201
    return user, conversation.json()
