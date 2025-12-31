"""
Module 4: Prescription Recommendation Engine

This module uses AI semantic similarity to recommend medicines based on
patient symptoms extracted from the transcript.
"""

import json
import os
import logging
from typing import List, Dict, Tuple
import google.generativeai as genai
from modules.utils.perf import Timer, get_records
from scipy.spatial.distance import cosine  # retained for possible numerical fallbacks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def prefilter_medicines(symptoms: str, medicines: List[Dict], k: int = 15) -> List[Dict]:
    """Quick pre-filter medicines by TF-IDF similarity to symptoms.

    Tries a TF-IDF vectorizer to compute cosine similarity and returns the
    top-k most relevant medicines. Falls back to a token-match heuristic if
    scikit-learn isn't available or the TF-IDF step fails.
    """
    if not symptoms or not medicines:
        return medicines

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(max_features=2000)
        corpus = [symptoms] + [m.get('description', '') or m['name'] for m in medicines]
        X = vec.fit_transform(corpus).toarray()
        sym_v = X[0]
        meds_v = X[1:]

        scores = []
        for v in meds_v:
            try:
                sim = 1.0 - cosine(sym_v, v)
                if sim != sim:
                    sim = 0.0
            except Exception:
                sim = 0.0
            scores.append(sim)

        idxs = sorted(range(len(medicines)), key=lambda i: scores[i], reverse=True)
        topk = idxs[:min(k, len(idxs))]
        return [medicines[i] for i in topk]
    except Exception:
        # Fallback: token overlap heuristic
        tokens = set([t for t in symptoms.lower().split() if len(t) > 3])
        scored = []
        for i, m in enumerate(medicines):
            text = (m.get('description', '') + ' ' + m.get('name', '')).lower()
            count = sum(1 for t in tokens if t in text)
            scored.append((count, i))
        scored.sort(key=lambda x: x[0], reverse=True)
        topk = [i for _, i in scored[:min(k, len(scored))]]
        return [medicines[i] for i in topk]


def get_medicine_recommendations(
    json_transcript_path: str,
    available_medicines: List[Dict],
    top_n: int = 5,
    prefilter_k: int = 15
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
        
        with Timer('read_transcript'):
            with open(json_transcript_path, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
        
        transcript_text = transcript_data.get('transcript', '')
        
        if not transcript_text:
            logger.warning("Transcript is empty")
            return []
        
        # Step 2: Extract symptom summary using LLM
        logger.info("Extracting symptom summary from transcript...")
        with Timer('extract_symptoms'):
            symptom_summary = extract_symptom_summary(transcript_text)
        
        if not symptom_summary:
            logger.warning("No symptoms extracted from transcript")
            return []
        
        logger.info(f"Symptom summary: {symptom_summary}")
        
        # Step 3: Pre-filter medicines to a smaller candidate set to reduce latency
        try:
            filtered_medicines = prefilter_medicines(symptom_summary, available_medicines, k=prefilter_k)
            logger.info(f'Prefiltered medicines: {len(available_medicines)} -> {len(filtered_medicines)}')
        except Exception as e:
            logger.warning(f'Prefilter step failed, continuing with full set: {e}')
            filtered_medicines = available_medicines

        # Use the filtered list for Gemini scoring
        medicines_for_gemini = filtered_medicines

        api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
        # If not set in env, attempt to load from .env file in repo root
        if not api_key:
            envpath = os.path.join(os.path.dirname(__file__), '..', '.env')
            envpath = os.path.abspath(envpath)
            if os.path.exists(envpath):
                with open(envpath, 'r', encoding='utf-8') as f:
                    for line in f:
                        line=line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            k,v=line.split('=',1)
                            os.environ.setdefault(k.strip(), v.strip())
                api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')

        if not api_key:
            logger.error('GEMINI_API_KEY is required for Gemini-only recommendations')
            raise RuntimeError('GEMINI_API_KEY not set')

        try:
            if hasattr(genai, 'configure'):
                genai.configure(api_key=api_key)
        except Exception as e:
            logger.debug(f"genai.configure not available or failed: {e}")

        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
        except Exception as e:
            logger.error(f'Gemini model unavailable: {e}')
            raise RuntimeError('Gemini model unavailable')

        # Build medicines list text (for the filtered candidate set)
        medicine_texts = [f"{med['name']}: {med.get('description','')}" for med in medicines_for_gemini]
        medicine_names = [med['name'] for med in medicines_for_gemini]

        if not medicine_texts:
            logger.warning('No medicines available in database')
            return []

        # Construct a prompt asking for JSON scores between 0.0 and 1.0
        meds_block = "\n".join([f"- {text}" for text in medicine_texts])
        prompt = (
            "You are a medical relevance assistant. Given a concise symptom summary and a list of medicines with descriptions, "
            "rate how relevant each medicine is for treating the symptoms on a scale from 0.0 to 1.0. "
            "Respond with valid JSON array of objects with keys 'name' and 'score' (number between 0.0 and 1.0), nothing else. "
            "If unsure, use 0.0. Keep numbers to two decimal places."
        )

        full_prompt = f"SYMPTOMS:\n{symptom_summary}\n\nMEDICINES:\n{meds_block}\n\n{prompt}"

        gen_cfg = None
        try:
            gen_cfg = genai.GenerationConfig(temperature=0.0, max_output_tokens=2048)
        except Exception:
            gen_cfg = None

        # Call Gemini
        try:
            with Timer('gemini_recommend_generate'):
                if gen_cfg is not None:
                    response = model.generate_content(contents=[full_prompt], generation_config=gen_cfg)
                else:
                    response = model.generate_content(contents=[full_prompt])
        except Exception as e:
            logger.error(f'Gemini recommendation call failed: {e}', exc_info=True)
            raise RuntimeError('Gemini recommendation call failed')

        # Extract text
        resp_text = getattr(response, 'text', None) or getattr(response, 'output', None) or ''
        if not resp_text and hasattr(response, 'candidates'):
            try:
                resp_text = response.candidates[0].content
            except Exception:
                resp_text = ''

        resp_text = (resp_text or '').strip()
        logger.info(f'Gemini recommendation response: {resp_text[:500]}')

        # Parse JSON from response (strip code fences or markdown if present)
        try:
            import re
            with Timer('parse_recommendation'):
                # Attempt to extract the first JSON array in the text
                start = resp_text.find('[')
                end = resp_text.rfind(']')
                cleaned = resp_text if start == -1 or end == -1 else resp_text[start:end+1]
                # If still empty, remove markdown fences
                if not cleaned.strip():
                    cleaned = re.sub(r'```.*?```', '', resp_text, flags=re.S).strip()
                parsed = json.loads(cleaned)
                if not isinstance(parsed, list):
                    raise ValueError('Parsed response is not a list')
                similarities = []
                for item in parsed:
                    name = item.get('name')
                    score = float(item.get('score', 0.0))
                    similarities.append((name, score))
        except Exception as e:
            logger.error(f'Failed to parse Gemini response as JSON: {e} -- raw response: {resp_text[:500]}')
            # Fail fast in Gemini-only mode
            raise RuntimeError('Could not parse Gemini recommendations')

        # Log perf records for visibility
        try:
            from modules.utils.perf import get_records
            perf_list = get_records(reset=True)
            logger.info("Performance timings: " + ", ".join(f"{k}={v:.3f}s" for k, v in perf_list))
        except Exception:
            pass

        # Map parsed results back to the original medicine set (fill 0.0 for non-candidates)
        parsed_map = {name: score for name, score in similarities}

        all_similarities = []
        for med in available_medicines:
            score = float(parsed_map.get(med['name'], 0.0))
            all_similarities.append((med['name'], score))

        # Sort and return top N
        all_similarities.sort(key=lambda x: x[1], reverse=True)
        top_recommendations = all_similarities[:top_n]
        logger.info(f'✓ Generated {len(top_recommendations)} recommendations via Gemini (prefilter_k={prefilter_k})')
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
