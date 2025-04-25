import pytest

from core.summarizer import Summarizer

class DummyExtractor:
    def __init__(self, text_to_return):
        self.text_to_return = text_to_return
    def extract_text_from_file(self, file_path):
        return self.text_to_return

class DummyLLM:
    def __init__(self, summary_to_return):
        self.summary_to_return = summary_to_return
    def summarize(self, text):
        return self.summary_to_return

@pytest.mark.parametrize('extracted,expected', [
    (None, 'Could not extract text from file.'),
    ('', 'Could not extract text from file.'),
    ('some text', 'Could not generate summary.'),
])
def test_summarizer_failures(monkeypatch, extracted, expected):
    # Setup dummy extractor always returning extracted
    summ = Summarizer.__new__(Summarizer)
    summ.extractor = DummyExtractor(extracted)
    # For generate summary: if extracted is truthy, return None to simulate failure
    llm_response = None
    if extracted:
        llm_response = None
    summ.llm = DummyLLM(llm_response)
    result = summ.summarize_file('fakepath')
    assert result == expected

def test_summarizer_success():
    summ = Summarizer.__new__(Summarizer)
    summ.extractor = DummyExtractor('text input')
    summ.llm = DummyLLM('my summary')
    res = summ.summarize_file('fake')
    assert res == 'my summary'