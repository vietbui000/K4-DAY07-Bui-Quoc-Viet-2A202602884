import pytest
from src.groq_runtime import GroqRuntime


def test_groq_requires_own_key(monkeypatch):
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    monkeypatch.setenv('GEMINI_API_KEY', 'different-provider-key')
    with pytest.raises(ValueError, match='GROQ_API_KEY'):
        GroqRuntime()


def test_groq_generation_and_model_check(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'test-only')
    client = GroqRuntime()
    requests = []
    def fake(endpoint, payload=None):
        requests.append((endpoint, payload))
        if endpoint == 'models':
            return {'data': [{'id': client.llm_model}]}
        return {'choices': [{'finish_reason': 'stop', 'message': {'content': 'Answer [1]'}}]}
    monkeypatch.setattr(client, '_request', fake)
    client.check_access()
    assert client.generate('question') == 'Answer [1]'
    assert requests[-1][1]['messages'][-1]['content'] == 'question'


def test_groq_rejects_incomplete_answer(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'test-only')
    client = GroqRuntime()
    monkeypatch.setattr(client, '_request', lambda *args: {'choices': [{'finish_reason': 'length'}]})
    with pytest.raises(RuntimeError, match='truncated'):
        client.generate('question')
