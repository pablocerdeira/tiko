import os
import tempfile
import pytest

from core.extractor import Extractor

class DummyExtractor(Extractor):
    def __init__(self, config):
        super().__init__(config)
        self.calls = []

    def _extract_text_with_tika(self, file_path):
        self.calls.append('tika')
        return 'text from tika'

    def _extract_text_with_tika_ocr(self, file_path):
        self.calls.append('tika_ocr')
        return 'text from ocr'

    def _extract_text_with_whisper(self, file_path):
        self.calls.append('whisper')
        return 'text from whisper'

@pytest.fixture
def extractor(tmp_path):
    # minimal config
    cfg = {
        'tika': {'url': 'http://tika', 'ocr_language': 'eng'},
        'whisper': {'enabled': True, 'provider': 'local', 'language': 'en'}
    }
    return DummyExtractor(cfg)

@pytest.mark.parametrize('ext,expected', [
    ('.pdf', 'tika'),
    ('.docx', 'tika'),
    ('.txt', 'tika'),
    ('.jpg', 'tika_ocr'),
    ('.png', 'tika_ocr'),
    ('.mp3', 'whisper'),
    ('.wav', 'whisper'),
])
def test_extract_dispatch(ext, expected, extractor, tmp_path):
    # create dummy file with extension
    file_path = tmp_path / f'dummy{ext}'
    file_path.write_text('dummy')
    # call extract_text_from_file
    result = extractor.extract_text_from_file(str(file_path))
    # check method was called
    assert extractor.calls == [expected]
    # check returned text
    assert result.startswith('text')

def test_extract_unsupported(extractor, tmp_path):
    # any unsupported extension should return an unsupported message
    file_path = tmp_path / 'dummy.unsupported'
    file_path.write_text('dummy')
    result = extractor.extract_text_from_file(str(file_path))
    assert result == 'Unsupported file format'

def test_whisper_disabled(tmp_path):
    # whisper disabled in config
    cfg = {'tika': {'url': '', 'ocr_language': 'eng'}, 'whisper': {'enabled': False}}
    ext = Extractor(cfg)
    # create audio file
    file_path = tmp_path / 'audio.mp3'
    file_path.write_text('dummy')
    res = ext.extract_text_from_file(str(file_path))
    assert res == 'Whisper transcription not available'