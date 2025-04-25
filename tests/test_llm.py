import pytest
import requests

from core.llm import LLM

class DummyResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise requests.HTTPError(f"Status {self.status_code}")
    def json(self):
        return self._json

@pytest.fixture
def config(tmp_path):
    # Provide minimal llm config with two providers
    return {
        'llm': {
            'provider': 'openai',
            'providers': {
                'openai': {
                    'url': 'http://api.openai/v1/chat/completions',
                    'api_key': 'KEY',
                    'model': 'gpt-test',
                    'system_prompt': 'SYS',
                    'temperature': 0.5,
                    'max_tokens': 10
                },
                'other': {
                    'url': 'http://api.other/complete',
                    'model': 'oth-test'
                }
            }
        }
    }

def test_summarize_chat(monkeypatch, config):
    llm = LLM(config)
    # Mock response data: chat style
    mock_data = {'choices': [{'message': {'content': ' summary text '}}]}
    monkeypatch.setattr(requests, 'post', lambda url, headers, json: DummyResponse(mock_data))
    out = llm.summarize('input text')
    assert out == 'summary text'

def test_summarize_completion(monkeypatch, config):
    # Use other provider without system prompt
    config['llm']['provider'] = 'other'
    llm = LLM(config)
    # Mock completion style
    mock_data = {'choices': [{'text': ' comp '}]}  
    monkeypatch.setattr(requests, 'post', lambda url, headers, json: DummyResponse(mock_data))
    out = llm.summarize('input text')
    assert out == 'comp'

def test_summarize_error(monkeypatch, config):
    llm = LLM(config)
    # Return error status
    monkeypatch.setattr(requests, 'post', lambda url, headers, json: DummyResponse({}, status_code=500))
    out = llm.summarize('foo')
    assert out is None