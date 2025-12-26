
import logging
import json
import numpy as np
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock database
class MockDB:
    def get_all_medicines(self):
        return [
            {"name": "Paracetamol", "description": "Analgesic and antipyretic for fever and pain", "stock_level": 100},
            {"name": "Amoxicillin", "description": "Antibiotic for bacterial infections", "stock_level": 50},
            {"name": "Cetirizine", "description": "Antihistamine for allergies and runny nose", "stock_level": 80},
            {"name": "Ibuprofen", "description": "NSAID for pain and inflammation", "stock_level": 60},
            {"name": "Cough Syrup", "description": "For cough relief", "stock_level": 40}
        ]
    
    def get_all_patients(self):
        return []

# Import ensemble
from modules.ensemble_engine import EnsembleRecommender

def test_ensemble():
    try:
        print("\n--- Testing Ensemble Recommender ---")
        
        # Initialize
        db = MockDB()
        ensemble = EnsembleRecommender(db_connection=db, parallel_execution=False)
        ensemble.set_database(db)
        
        # Test input
        symptoms = "I have a high fever and headache"
        medicines = db.get_all_medicines()
        
        print(f"\nInput Symptoms: '{symptoms}'")
        medicines_str = [m['name'] for m in medicines]
        print(f"Medicines: {medicines_str}")
        
        # Run recommendations
        recs = ensemble.get_recommendations(symptoms, medicines, top_n=5)
        
        print(f"\nGenerated {len(recs)} recommendations")
        
        for i, rec in enumerate(recs):
            print(f"\n{i+1}. {rec['name']}")
            print(f"   Final Score: {rec['final_score']}")
            voting = rec.get('voting', {})
            print(f"   Voting: {json.dumps(voting, indent=2)}")
            
            # Check for zeros
            scores = list(voting.values())
            if all(s == 0 for s in scores):
                print("   [WARNING] ALL SCORES ARE ZERO")
            else:
                print("   [OK] Has non-zero scores")

    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ensemble()
