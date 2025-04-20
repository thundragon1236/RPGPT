import os
from dotenv import load_dotenv
load_dotenv()

# Explicitly set OpenRouter credentials for tests
os.environ["OR_API_KEY"] = os.getenv("OR_API_KEY") or "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"
os.environ["OR_MODEL"] = os.getenv("OR_MODEL") or "google/gemini-2.5-flash-preview"
os.environ["OR_ENDPOINT"] = os.getenv("OR_ENDPOINT") or "https://openrouter.ai/api/v1/chat/completions"

import pytest
import json
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    rv = client.get('/')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['message'].startswith('LifeQuest')

def test_suggest_xp_valid(client):
    payload = {
        "daily_log": "ran 5km and read a chapter",
        "character": {"id": "tester", "stats": {}, "skills": {}}
    }
    rv = client.post('/suggest_xp', data=json.dumps(payload), content_type='application/json')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'suggestions' in data


def test_suggest_xp_missing_fields(client):
    rv = client.post('/suggest_xp', data=json.dumps({}), content_type='application/json')
    assert rv.status_code == 400
    data = rv.get_json()
    assert 'error' in data

def test_get_stats_and_skills(client):
    # First, save some progress to create the character
    payload = {
        "character_id": "tester",
        "daily_log": "ran 5km",
        "suggestions": [
            {"activity": "ran 5km", "stat_xp": {"vitality": 10}, "skill": "running", "skill_xp": 10}
        ]
    }
    rv = client.post('/save_progress', data=json.dumps(payload), content_type='application/json')
    assert rv.status_code == 200
    # Now test get_stats
    rv = client.get('/get_stats?character_id=tester')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'stats' in data
    # Now test list_skills
    rv = client.get('/list_skills?character_id=tester')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'skills' in data


def test_save_progress_missing_fields(client):
    rv = client.post('/save_progress', data=json.dumps({}), content_type='application/json')
    assert rv.status_code == 400
    data = rv.get_json()
    assert 'error' in data
