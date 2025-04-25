import os
import pytest
import requests

from core.extractor import Extractor

# Load configuration
import json
cfg = json.load(open('config.json'))

@pytest.fixture(scope='module')
def extractor():
    return Extractor(cfg)

def is_tika_up():
    try:
        url = cfg['tika']['url'].rstrip('/') + '/version'
        r = requests.get(url, timeout=2)
        r.raise_for_status()
        return True
    except Exception:
        return False

def has_whisper(extractor):
    return getattr(extractor, 'whisper_enabled', False) and getattr(extractor, 'whisper_model', None) is not None

@pytest.mark.skipif(not is_tika_up(), reason="Tika server is not reachable")
@pytest.mark.parametrize('filename', [f for f in os.listdir('test_files') 
                                      if os.path.splitext(f)[1].lower() 
                                         in ['.pdf','.docx','.xlsx','.html','.md','.txt', '.jpeg','.jpg','.png','.gif']])
def test_extract_documents(extractor, filename):
    """
    Integration test: extract text via Tika for document and image files.
    """
    path = os.path.join('test_files', filename)
    text = extractor.extract_text_from_file(path)
    assert text is not None
    # Expect some non-empty string (images may OCR empty)
    assert isinstance(text, str)

@pytest.mark.skipif(not has_whisper(Extractor(cfg)), reason="Whisper model not available")
@pytest.mark.parametrize('filename', [f for f in os.listdir('test_files') 
                                      if os.path.splitext(f)[1].lower() 
                                         in ['.mp3','.wav','.m4a','.flac','.aac','.ogg']])
def test_transcribe_audio(extractor, filename):
    """
    Integration test: transcribe audio via Whisper local.
    """
    path = os.path.join('test_files', filename)
    text = extractor.extract_text_from_file(path)
    assert text is not None
    assert isinstance(text, str)