import json
from modules.recommendation_module import prefilter_medicines


def test_prefilter_tf_idf_simple():
    symptoms = "Patient has fever and headache"
    meds = []
    # create 20 meds, first few mention fever
    for i in range(20):
        if i < 3:
            desc = "fever reducer for high fever"
            name = f"FeverMed{i}"
        else:
            desc = f"general med {i}"
            name = f"Med{i}"
        meds.append({'name': name, 'description': desc})

    filtered = prefilter_medicines(symptoms, meds, k=5)
    assert len(filtered) <= 5
    # ensure that at least one fever med is included
    assert any('FeverMed' in m['name'] for m in filtered)


def test_prefilter_fallback_tokens():
    symptoms = "chronic back pain"
    meds = [{'name': 'PainAway', 'description': 'back pain relief'}, {'name': 'Other', 'description': 'not related'}]
    filtered = prefilter_medicines(symptoms, meds, k=2)
    assert len(filtered) == 2
    assert filtered[0]['name'] == 'PainAway' or filtered[1]['name'] == 'PainAway'