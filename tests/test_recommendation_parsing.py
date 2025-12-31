import os
import json
import types
import pytest
import modules.recommendation_module as rm
import modules.recommenders.semantic_recommender as sr


class DummyRespText:
    def __init__(self, text):
        self.text = text


class DummyModel:
    def __init__(self, name):
        self.name = name

    def generate_content(self, contents=None, generation_config=None):
        # Default: return empty
        return DummyRespText('')


@pytest.fixture
def enable_gemini(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'testkey')
    dummy = types.SimpleNamespace()
    dummy.upload_file = lambda path: 'uploaded_file_obj'
    dummy.GenerativeModel = DummyModel
    monkeypatch.setattr(rm, 'genai', dummy)
    yield


def test_recommendations_parses_valid_json(enable_gemini, tmp_path, monkeypatch):
    # Prepare a test transcript file
    test_transcript = {
        "patient_id": "T1",
        "doctor_id": "D1",
        "conversation_timestamp": "2025-11-15T12:00:00",
        "transcript": "Patient has fever and headache"
    }
    tpath = tmp_path / 'test_transcript.json'
    with open(tpath, 'w', encoding='utf-8') as f:
        json.dump(test_transcript, f)

    # Create dummy medicines
    meds = [
        {'name': 'Paracetamol', 'description': 'pain relief and fever reducer', 'stock_level': 50, 'prescription_frequency': 1},
        {'name': 'Ibuprofen', 'description': 'anti-inflammatory', 'stock_level': 20, 'prescription_frequency': 1}
    ]

    # Patch model generate_content to return valid JSON
    def gen_generate(self, contents=None, generation_config=None):
        return DummyRespText('[{"name": "Paracetamol", "score": 0.95}, {"name": "Ibuprofen", "score": 0.45}]')

    monkeypatch.setattr(rm.genai.GenerativeModel, 'generate_content', gen_generate, raising=False)

    recs = rm.get_medicine_recommendations(str(tpath), meds, top_n=2)
    assert isinstance(recs, list)
    assert recs[0][0] == 'Paracetamol'
    assert abs(recs[0][1] - 0.95) < 1e-6


def test_recommendations_parses_fenced_json(enable_gemini, tmp_path, monkeypatch):
    test_transcript = {"transcript": "nausea and dizziness"}
    tpath = tmp_path / 'test_transcript2.json'
    with open(tpath, 'w', encoding='utf-8') as f:
        json.dump(test_transcript, f)

    meds = [{'name': 'MedA', 'description': 'desc', 'stock_level': 5, 'prescription_frequency': 1}]

    def gen_generate(self, contents=None, generation_config=None):
        return DummyRespText('''```
[ {"name": "MedA", "score": 0.20} ]
```''')

    monkeypatch.setattr(rm.genai.GenerativeModel, 'generate_content', gen_generate, raising=False)

    recs = rm.get_medicine_recommendations(str(tpath), meds, top_n=1)
    assert recs and recs[0][0] == 'MedA'


def test_recommendations_malformed_json_returns_empty(enable_gemini, tmp_path, monkeypatch):
    test_transcript = {"transcript": "some symptoms"}
    tpath = tmp_path / 'test_transcript3.json'
    with open(tpath, 'w', encoding='utf-8') as f:
        json.dump(test_transcript, f)

    meds = [{'name': 'MedB', 'description': 'desc', 'stock_level': 5, 'prescription_frequency': 1}]

    def gen_generate(self, contents=None, generation_config=None):
        return DummyRespText('NOT JSON AT ALL')

    monkeypatch.setattr(rm.genai.GenerativeModel, 'generate_content', gen_generate, raising=False)

    recs = rm.get_medicine_recommendations(str(tpath), meds, top_n=1)
    assert recs == []


def test_semantic_recommender_returns_scores(enable_gemini, monkeypatch):
    import numpy as _np
    meds = [{'name': 'A', 'description': 'painkiller'}, {'name': 'B', 'description': 'antibiotic'}]

    # Provide a deterministic local model via monkeypatching the _model property
    class DummyModel:
        def encode(self, texts, convert_to_numpy=True):
            # Return embeddings such that A is more similar to the symptoms than B
            out = []
            for t in texts:
                if isinstance(t, str) and 'severe' in t:
                    out.append([1.0, 0.0])
                elif isinstance(t, str) and 'painkiller' in t:
                    out.append([0.9, 0.1])
                else:
                    out.append([0.1, 0.9])
            return _np.array(out)

    recommender = sr.SemanticRecommender()
    monkeypatch.setattr(recommender, '_model', DummyModel(), raising=False)

    scores = recommender.recommend('severe pain and fever', meds)
    assert hasattr(scores, 'shape')
    assert len(scores) == 2
    assert scores[0] > scores[1]

