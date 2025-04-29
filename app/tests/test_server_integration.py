import io
import os
import pytest
from unittest.mock import patch

from api import server
from core.web_extractor import get_input_file as original_get_input_file

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
    
    # Patch get_input_file to work with test client
    def mock_get_input_file(req, upload_folder):
        """Test version of get_input_file that works with Flask test client"""
        if 'file' not in req.files:
            return None
        file = req.files['file']
        if file.filename == '':
            return None
        file_path = os.path.join(upload_folder, file.filename)
        file.save(file_path)
        return file_path
        
    monkeypatch.setattr(server, 'get_input_file', mock_get_input_file)
    
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
    assert b'No file or URL provided' in resp.data

def test_summary_empty_filename(client):
    # file part present but filename empty
    data = {'file': (io.BytesIO(b'data'), '')}
    resp = client.post('/summary', data=data, content_type='multipart/form-data')
    assert resp.status_code == 400
    assert b'No file or URL provided' in resp.data

def test_summary_success(client):
    # send a valid file
    data = {'file': (io.BytesIO(b'hello'), 'test.txt')}
    resp = client.post('/summary', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert resp.data == b'dummy summary'
    
    # Uploaded file should be removed
    files = os.listdir(server.app.config['UPLOAD_FOLDER'])
    assert files == []