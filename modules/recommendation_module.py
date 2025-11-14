"""
Module 4: Prescription Recommendation Engine

This module uses AI semantic similarity to recommend medicines based on
patient symptoms extracted from the transcript.
"""

import json
import os
import logging
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_medicine_recommendations(
    json_transcript_path: str,
    available_medicines: List[Dict],
    top_n: int = 5
) -> List[Tuple[str, float]]:
    """
    Recommend medicines based on semantic similarity between patient symptoms
    and medicine descriptions.
    
    Args:
        json_transcript_path (str): Path to the JSON transcript file
        available_medicines (List[Dict]): List of medicine dictionaries from database
        top_n (int): Number of top recommendations to return (default: 5)
    
    Returns:
        List[Tuple[str, float]]: List of (medicine_name, similarity_score) tuples,
                                  sorted by similarity (highest first)
    
    Example:
        >>> medicines = db.get_all_medicines()
        >>> recommendations = get_medicine_recommendations('transcript.json', medicines)
        >>> print(recommendations)
        [('Paracetamol', 0.85), ('Ibuprofen', 0.78), ...]
    """
    
    try:
        # Step 1: Read the transcript
        logger.info(f"Reading transcript from: {json_transcript_path}")
        
        if not os.path.exists(json_transcript_path):
            raise FileNotFoundError(f"Transcript file not found: {json_transcript_path}")
        
        with open(json_transcript_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        transcript_text = transcript_data.get('transcript', '')
        
        if not transcript_text:
            logger.warning("Transcript is empty")
            return []
        
        # Step 2: Extract symptom summary using LLM
        logger.info("Extracting symptom summary from transcript...")
        symptom_summary = extract_symptom_summary(transcript_text)
        
        if not symptom_summary:
            logger.warning("No symptoms extracted from transcript")
            return []
        
        logger.info(f"Symptom summary: {symptom_summary}")
        
        # Step 3: Load sentence transformer model
        logger.info("Loading sentence transformer model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✓ Model loaded successfully")
        
        # Step 4: Generate embedding for symptom summary
        logger.info("Generating embeddings...")
        symptom_embedding = model.encode(symptom_summary, convert_to_tensor=False)
        
        # Step 5: Generate embeddings for all available medicines
        medicine_texts = []
        medicine_names = []
        
        for med in available_medicines:
            # Combine name and description for better matching
            med_text = f"{med['name']}: {med['description']}"
            medicine_texts.append(med_text)
            medicine_names.append(med['name'])
        
        if not medicine_texts:
            logger.warning("No medicines available in database")
            return []
        
        medicine_embeddings = model.encode(medicine_texts, convert_to_tensor=False)
        
        # Step 6: Calculate cosine similarity
        logger.info("Calculating similarity scores...")
        similarities = []
        
        for i, med_embedding in enumerate(medicine_embeddings):
            # Cosine similarity = 1 - cosine distance
            similarity = 1 - cosine(symptom_embedding, med_embedding)
            similarities.append((medicine_names[i], similarity))
        
        # Step 7: Sort by similarity (highest first) and return top N
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_recommendations = similarities[:top_n]
        
        logger.info(f"✓ Generated {len(top_recommendations)} recommendations")
        
        return top_recommendations
        
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}", exc_info=True)
        return []


def extract_symptom_summary(transcript_text: str) -> str:
    """
    Extract a concise symptom summary from the transcript using Gemini AI.
    
    Args:
        transcript_text (str): The conversation transcript
    
    Returns:
        str: Concise summary of patient's symptoms and medical conditions
    """
    
    try:
        # Get API key from environment variable
        api_key = os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            logger.warning("GEMINI_API_KEY not set, using simple extraction")
            # Fallback to simple extraction if no API key
            return extract_symptom_summary_simple(transcript_text)
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Create prompt for symptom extraction
        prompt = f"""
You are a medical symptom extraction assistant. Read this doctor-patient conversation 
and extract ONLY the medical symptoms, conditions, and complaints.

TRANSCRIPT:
"{transcript_text}"

YOUR TASK:
Create a brief, concise summary (1-2 sentences maximum) that lists ONLY:
- Symptoms (fever, headache, pain, nausea, etc.)
- Medical conditions (diabetes, hypertension, asthma, etc.)
- Complaints (fatigue, dizziness, weakness, etc.)

Do NOT include:
- Allergies
- Lifestyle information
- Patient demographic details

Output ONLY the symptom summary, nothing else. Be concise and medical.

EXAMPLE OUTPUT:
"Patient reports severe headache for 3 days, accompanied by nausea and sensitivity to light."
"""
        
        logger.info("Calling Gemini AI for symptom extraction...")
        response = model.generate_content(prompt)
        summary = response.text.strip()
        
        logger.info(f"✓ Gemini extracted symptoms: {summary}")
        return summary
        
    except Exception as e:
        logger.warning(f"Error using Gemini, falling back to simple extraction: {e}")
        return extract_symptom_summary_simple(transcript_text)


def extract_symptom_summary_simple(transcript_text: str) -> str:
    """
    Simple keyword-based symptom extraction (fallback method).
    
    Args:
        transcript_text (str): The conversation transcript
    
    Returns:
        str: Simple symptom summary
    """
    
    # Common medical keywords to look for
    symptom_keywords = [
        'pain', 'ache', 'fever', 'headache', 'nausea', 'vomit', 'dizzy', 
        'tired', 'fatigue', 'weak', 'cough', 'cold', 'flu', 'sore',
        'diabetes', 'hypertension', 'asthma', 'infection', 'inflammation',
        'swelling', 'rash', 'itch', 'burn', 'bleed', 'bruise'
    ]
    
    text_lower = transcript_text.lower()
    found_symptoms = []
    
    for keyword in symptom_keywords:
        if keyword in text_lower:
            found_symptoms.append(keyword)
    
    if found_symptoms:
        summary = f"Patient mentions: {', '.join(found_symptoms)}"
    else:
        # Use the full transcript as fallback
        summary = transcript_text[:200]  # First 200 characters
    
    logger.info(f"Simple extraction: {summary}")
    return summary


def display_recommendations(
    recommendations: List[Tuple[str, float]],
    available_medicines: List[Dict]
) -> None:
    """
    Display recommendations in a formatted way with medicine details.
    
    Args:
        recommendations: List of (medicine_name, similarity_score) tuples
        available_medicines: List of all medicine dictionaries
    """
    
    # Create a lookup dictionary for medicine details
    medicine_lookup = {med['name']: med for med in available_medicines}
    
    print("\n" + "="*70)
    print("💊 TOP MEDICINE RECOMMENDATIONS")
    print("="*70 + "\n")
    
    for rank, (medicine_name, similarity_score) in enumerate(recommendations, 1):
        med = medicine_lookup.get(medicine_name)
        
        if med:
            print(f"#{rank}. {medicine_name}")
            print(f"    Similarity Score: {similarity_score:.2%}")
            print(f"    Description: {med['description']}")
            print(f"    Stock Level: {med['stock_level']} units")
            print(f"    Prescribed: {med['prescription_frequency']} times")
            
            # Stock warning
            if med['stock_level'] < 10:
                print(f"    ⚠️  LOW STOCK - Consider alternative")
            
            print()


# Demo/Testing
if __name__ == '__main__':
    # Load environment variables for Gemini API
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from load_env import load_env
        load_env()
    except ImportError:
        logger.warning("load_env not available, using system environment variables")
    
    from modules.database_module import MedicineDatabase
    
    print("\n" + "="*70)
    print("🤖 PRESCRIPTION RECOMMENDATION ENGINE - DEMO")
    print("="*70 + "\n")
    
    # Initialize database
    print("📊 Loading medicine database...")
    db = MedicineDatabase('pharmacy.db')
    
    # Get all available medicines
    available_medicines = db.get_all_medicines()
    print(f"✓ Loaded {len(available_medicines)} medicines from database\n")
    
    # Display available medicines
    print("Available medicines:")
    for med in available_medicines:
        print(f"  - {med['name']}: {med['description']}")
    
    # Create a test transcript with symptoms
    print("\n" + "="*70)
    print("📝 CREATING TEST TRANSCRIPT")
    print("="*70 + "\n")
    
    test_transcript = {
        "patient_id": "TEST001",
        "doctor_id": "DOC001",
        "conversation_timestamp": "2025-11-15T12:00:00",
        "transcript": "Doctor, I've been having severe headaches for the past 3 days. "
                     "I also have fever and body aches. The pain is really bad, especially "
                     "in my forehead area. I feel very tired and weak."
    }
    
    print(f"Symptoms: {test_transcript['transcript']}\n")
    
    # Save test transcript
    test_transcript_path = 'test_transcript_recommendation.json'
    with open(test_transcript_path, 'w') as f:
        json.dump(test_transcript, f, indent=2)
    
    print(f"✓ Test transcript saved to: {test_transcript_path}\n")
    
    # Get recommendations
    print("="*70)
    print("🔍 ANALYZING SYMPTOMS & GENERATING RECOMMENDATIONS")
    print("="*70 + "\n")
    
    recommendations = get_medicine_recommendations(
        test_transcript_path,
        available_medicines,
        top_n=5
    )
    
    # Display recommendations
    if recommendations:
        display_recommendations(recommendations, available_medicines)
        
        print("="*70)
        print("📋 RECOMMENDATION SUMMARY")
        print("="*70 + "\n")
        
        print("Based on symptoms: headache, fever, body aches, pain, fatigue")
        print("\nTop 3 recommended medicines:")
        for rank, (medicine, score) in enumerate(recommendations[:3], 1):
            print(f"  {rank}. {medicine} (Match: {score:.1%})")
    else:
        print("⚠️ No recommendations generated")
    
    # Clean up
    db.close_connection()
    
    # Clean up test file
    if os.path.exists(test_transcript_path):
        os.remove(test_transcript_path)
        print(f"\n✓ Cleaned up test file: {test_transcript_path}")
    
    print("\n" + "="*70)
    print("✅ Demo completed!")
    print("="*70 + "\n")
