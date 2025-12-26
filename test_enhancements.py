"""
Test script for new EHR system enhancements
Tests: Ensemble recommender, XAI, and FL simulation
"""

import logging
logging.basicConfig(level=logging.INFO)

print("=" * 60)
print("Testing EHR System Enhancements")
print("=" * 60)

# Test 1: Federated Learning Simulation
print("\n[1] Testing Federated Learning Simulation...")
try:
    from modules.federated import FederatedSimulator
    from modules.federated.fl_config import DEMO_CONFIG
    
    sim = FederatedSimulator(config=DEMO_CONFIG)
    results = sim.run_simulation()
    
    print(f"  ✓ FL Simulation Complete")
    print(f"    Rounds: {results['total_rounds']}")
    print(f"    Clients: {results['num_clients']}")
    print(f"    Final Loss: {results['final_metrics']['avg_loss']}")
    print(f"    Final WER: {results['final_metrics']['avg_wer']}")
except Exception as e:
    print(f"  ✗ FL Simulation Error: {e}")

# Test 2: Ensemble Recommender
print("\n[2] Testing Ensemble Recommender...")
try:
    from modules.ensemble_engine import EnsembleRecommender
    
    ensemble = EnsembleRecommender(use_learnable_weights=True)
    
    # Test with mock data
    test_symptoms = "Patient reports fever, headache, and body pain"
    test_medicines = [
        {'name': 'Paracetamol', 'description': 'Pain relief and fever reducer', 'stock_level': 100, 'prescription_frequency': 50},
        {'name': 'Ibuprofen', 'description': 'Anti-inflammatory pain relief', 'stock_level': 80, 'prescription_frequency': 30},
        {'name': 'Aspirin', 'description': 'Pain and fever medicine', 'stock_level': 60, 'prescription_frequency': 20}
    ]
    
    recommendations = ensemble.get_recommendations(test_symptoms, test_medicines, top_n=3)
    
    print(f"  ✓ Ensemble Recommendations Generated")
    print(f"    Model Weights: {ensemble.get_model_weights()}")
    for rec in recommendations:
        print(f"    - {rec['name']}: {rec['final_score']:.2f}")
        print(f"      Votes: {rec['voting']}")
except Exception as e:
    print(f"  ✗ Ensemble Error: {e}")

# Test 3: XAI Engine
print("\n[3] Testing Explainability Engine...")
try:
    from modules.explainers import RecommendationExplainer
    
    xai = RecommendationExplainer(use_gemini=False)  # Skip Gemini for test
    
    # Test explanation
    test_rec = {'name': 'Paracetamol', 'description': 'Pain relief', 'final_score': 0.85, 'voting': {'semantic': 0.8, 'tfidf': 0.7}}
    explanation = xai.explain_recommendation(
        symptoms="Patient has fever and headache",
        medicine=test_rec,
        final_score=0.85,
        voting={'semantic': 0.8, 'tfidf': 0.7}
    )
    
    print(f"  ✓ Explanation Generated")
    print(f"    Primary Reason: {explanation['primary_reason']}")
    print(f"    Contributing Symptoms: {explanation['contributing_symptoms']}")
    print(f"    Confidence: {explanation['confidence']}")
except Exception as e:
    print(f"  ✗ XAI Error: {e}")

print("\n" + "=" * 60)
print("All Tests Complete!")
print("=" * 60)
