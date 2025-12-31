import os
import json
import tempfile
import types
import pytest

import modules.transcription_engine as te


class DummyResponseText:
    def __init__(self, text):
        self.text = text


class DummyResponseCandidates:
    def __init__(self, content):
        class C:
            def __init__(self, content):
                self.content = content
        self.candidates = [C(content)]


class DummyResponseDict:
    def __init__(self, text=None, candidates=None):
        self._d = {}
        if text is not None:
            self._d['text'] = text
        if candidates is not None:
            self._d['candidates'] = [{'content': candidates}]

    def __iter__(self):
        return iter(self._d)

    def get(self, k, default=None):
        return self._d.get(k, default)


@pytest.fixture
def tmp_audio_file():
    fd, path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    with open(path, 'wb') as f:
        f.write(b"RIFF....WAVE")
    yield path
    try:
        os.remove(path)
    except Exception:
        pass


@pytest.fixture
def enable_gemini(monkeypatch):
    # Force Gemini mode in the module
    monkeypatch.setattr(te, '_USE_GEMINI', True)
    # Provide a dummy genai module if not present
    dummy = types.SimpleNamespace()
    dummy.upload_file = lambda path: "uploaded_file_obj"

    class DummyModel:
        def __init__(self, name):
            self.name = name

        def generate_content(self, contents=None, generation_config=None):
            # Default behavior, to be monkeypatched in tests
            return DummyResponseText("default transcription")

    dummy.GenerativeModel = DummyModel
    monkeypatch.setattr(te, 'genai', dummy)
    yield


def test_transcribe_with_text_response(tmp_audio_file, enable_gemini, monkeypatch, tmp_path):
    # Patch the model to return a text attribute
    def gen_generate(self, contents=None, generation_config=None):
        return DummyResponseText("Speaker 1: Hello from test")

    monkeypatch.setattr(te.genai.GenerativeModel, 'generate_content', gen_generate, raising=False)

    out = te.transcribe_conversation(tmp_audio_file, 'P1', 'D1', output_dir=str(tmp_path))
    assert out is not None

    with open(out, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert 'transcript' in data
    assert 'Hello from test' in data['transcript']


def test_transcribe_with_candidates_response(tmp_audio_file, enable_gemini, monkeypatch, tmp_path):
    def gen_generate(self, contents=None, generation_config=None):
        return DummyResponseCandidates("Candidate transcript here")

    monkeypatch.setattr(te.genai.GenerativeModel, 'generate_content', gen_generate, raising=False)

    out = te.transcribe_conversation(tmp_audio_file, 'P2', 'D2', output_dir=str(tmp_path))
    assert out is not None

    with open(out, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert 'Candidate transcript' in data['transcript']


def test_transcribe_with_dict_response(tmp_audio_file, enable_gemini, monkeypatch, tmp_path):
    def gen_generate(self, contents=None, generation_config=None):
        return DummyResponseDict(text="Dict text here")

    monkeypatch.setattr(te.genai.GenerativeModel, 'generate_content', gen_generate, raising=False)

    out = te.transcribe_conversation(tmp_audio_file, 'P3', 'D3', output_dir=str(tmp_path))
    assert out is not None

    with open(out, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert 'Dict text here' in data['transcript']


def test_transcribe_with_empty_response_returns_none(tmp_audio_file, enable_gemini, monkeypatch):
    def gen_generate(self, contents=None, generation_config=None):
        return DummyResponseText("")

    monkeypatch.setattr(te.genai.GenerativeModel, 'generate_content', gen_generate, raising=False)

    out = te.transcribe_conversation(tmp_audio_file, 'P4', 'D4')
    assert out is None
