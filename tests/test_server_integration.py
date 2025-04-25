import io
import os
import pytest

from api import server

@pytest.fixture(autouse=True)
def client(monkeypatch, tmp_path):
    """
    Flask test client with dummy summarizer and isolated upload folder.
    """
    # Use temporary upload folder
    upload_folder = tmp_path / 'uploads'
    upload_folder.mkdir()
    server.app.config['UPLOAD_FOLDER'] = str(upload_folder)
    # Replace summarizer with dummy
    class DummySummarizer:
        def summarize_file(self, file_path):
            return 'dummy summary'
    monkeypatch.setattr(server, 'summarizer', DummySummarizer())
    # Create test client
    client = server.app.test_client()
    yield client

def test_health_endpoint(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.get_json() == {'status': 'ok'}

def test_summary_no_file(client):
    resp = client.post('/summary', data={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data

def test_summary_empty_filename(client):
    # file part present but filename empty
    data = {'file': (io.BytesIO(b'data'), '')}
    resp = client.post('/summary', data=data, content_type='multipart/form-data')
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data

def test_summary_success(client):
    # send a valid file
    data = {'file': (io.BytesIO(b'hello'), 'test.txt')}
    resp = client.post('/summary', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {'summary': 'dummy summary'}
    # Uploaded file should be removed
    # upload folder contains no files
    files = os.listdir(server.app.config['UPLOAD_FOLDER'])
    assert files == []