"""
Module 2: EHR Profile Auto-Filler (Gemini-Powered)

This module reads the JSON transcript and uses Google's Gemini AI to intelligently
extract medical information and fill in the patient's EHR profile.
"""

import json
import os
import logging
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def autofill_ehr(json_transcript_path, patient_ehr_template):
    """
    Automatically fills empty fields in a patient's EHR template using
    Gemini-powered intelligent extraction from the conversation transcript.
    
    Args:
        json_transcript_path (str): Path to the JSON file containing the transcript
        patient_ehr_template (dict): Dictionary with EHR fields (some may be empty)
    
    Returns:
        dict: Updated EHR dictionary with filled information,
              or None if operation fails
    
    Raises:
        ValueError: If input validation fails
        FileNotFoundError: If the JSON file doesn't exist
        Exception: For any other errors during processing
    """
    
    try:
        # Input Validation
        if not json_transcript_path or not isinstance(json_transcript_path, str):
            error_msg = "json_transcript_path must be a non-empty string"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not isinstance(patient_ehr_template, dict):
            error_msg = "patient_ehr_template must be a dictionary"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Verify JSON file exists
        if not os.path.exists(json_transcript_path):
            error_msg = f"JSON transcript file not found: {json_transcript_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        logger.info(f"Reading transcript from: {json_transcript_path}")
        
        # Read the JSON transcript file
        with open(json_transcript_path, 'r', encoding='utf-8') as json_file:
            transcript_data = json.load(json_file)
        
        # Extract the transcript text
        transcript_text = transcript_data.get('transcript', '')
        
        if not transcript_text:
            logger.warning("Transcript text is empty, returning template as-is")
            return patient_ehr_template
        
        logger.info("Using Gemini AI to analyze transcript for medical information...")
        
        # Create a copy of the template to avoid modifying the original
        updated_ehr = patient_ehr_template.copy()
        
        # Get empty fields that need to be filled
        # Handle both simple fields (strings) and complex fields (lists)
        empty_fields = {}
        for key, value in updated_ehr.items():
            if isinstance(value, list):
                if len(value) == 0:
                    empty_fields[key] = value
            elif isinstance(value, str):
                if not value or value.strip() == "":
                    empty_fields[key] = value
            elif value is None or value == "":
                empty_fields[key] = value
        
        if not empty_fields:
            logger.info("No empty fields to fill")
            return updated_ehr
        
        logger.info(f"Fields to fill: {list(empty_fields.keys())}")
        
        # Use Gemini to extract comprehensive medical information
        extracted_data = extract_with_gemini(transcript_text, list(empty_fields.keys()))
        
        # Update the EHR with extracted information (only if field is still empty)
        for field, value in extracted_data.items():
            if field in updated_ehr:
                # Check if field is still empty before updating
                current_value = updated_ehr[field]
                is_empty = False
                
                if isinstance(current_value, list):
                    is_empty = len(current_value) == 0
                elif isinstance(current_value, str):
                    is_empty = not current_value or current_value.strip() == ""
                elif current_value is None:
                    is_empty = True
                
                # Only update if field is empty and we extracted something
                if is_empty and value:
                    if isinstance(value, list) and len(value) > 0:
                        updated_ehr[field] = value
                        logger.info(f"✓ Filled '{field}' with {len(value)} items")
                    elif isinstance(value, str) and value.strip():
                        updated_ehr[field] = value
                        logger.info(f"✓ Filled '{field}': {value[:100]}...")
        
        return updated_ehr
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in autofill_ehr: {e}", exc_info=True)
        raise


def extract_with_gemini(transcript_text, fields_to_extract):
    """
    Uses Google's Gemini AI to intelligently extract medical information
    from the transcript text.
    
    Args:
        transcript_text (str): The conversation transcript
        fields_to_extract (list): List of field names to extract
    
    Returns:
        dict: Extracted information for each field
    """
    
    try:
        # Get API key from environment variable
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable not set")
            raise ValueError("GEMINI_API_KEY environment variable not set. "
                           "Get your API key from: https://aistudio.google.com/app/apikey")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Use Gemini 2.5 Flash model (stable, fast and efficient)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Determine what fields need to be extracted
        field_descriptions = {
            # Demographics (patient table fields)
            'gender': 'Patient gender (Male/Female/Other)',
            'insurance_info': 'Insurance provider or policy information',
            
            # EHR JSON fields - Vital Signs
            'vital_signs': 'List of vital sign measurements with dates (height, weight, BMI, blood pressure, pulse, temperature, respiratory rate)',
            
            # Clinical information
            'clinical_notes': 'List of clinical notes/observations from consultations with dates',
            'symptoms': 'Current symptoms, complaints, or medical conditions mentioned',
            'diagnoses': 'List of diagnoses or medical conditions identified',
            'medications': 'List of current medications with dosages and frequencies',
            
            # Medical history
            'allergies_mentioned': 'Drug allergies, food allergies, or environmental allergies',
            'procedures': 'List of medical procedures performed or planned',
            'immunizations': 'List of vaccines/immunizations mentioned',
            'lab_results': 'Laboratory test results with values and dates',
            'lifestyle_notes': 'Occupation, exercise, diet, smoking, alcohol use, sleep patterns'
        }
        
        # Build extraction prompt only for requested fields
        fields_section = ""
        for field in fields_to_extract:
            if field in field_descriptions:
                fields_section += f"- **{field}**: {field_descriptions[field]}\n"
        
        # Create a comprehensive prompt for medical information extraction
        prompt = f"""
You are an expert medical information extraction AI. Analyze this doctor-patient conversation and extract ALL relevant medical information.

TRANSCRIPT:
"{transcript_text}"

FIELDS TO EXTRACT:
{fields_section}

EXTRACTION GUIDELINES:

1. **Demographics**: Extract gender, insurance info if mentioned
2. **Vital Signs**: Format as list of objects with date, type, value, unit
   Example: {{"date": "2025-11-16", "type": "Blood Pressure", "value": "120/80", "unit": "mmHg"}}
3. **Clinical Notes**: Format as list with date, note text, and provider
4. **Diagnoses**: Format as list with date, condition name, and ICD code if mentioned
5. **Medications**: Format as list with name, dosage, frequency, start_date
6. **Lab Results**: Format as list with test_name, value, unit, reference_range, date, abnormal_flag
7. **Procedures**: Format as list with date, procedure name, notes
8. **Immunizations**: Format as list with vaccine name, date, provider

IMPORTANT RULES:
- Be INCLUSIVE - extract anything medically relevant
- For list fields (vital_signs, clinical_notes, etc.), return as JSON arrays
- For simple text fields (symptoms, allergies_mentioned, lifestyle_notes), return as strings
- If nothing is mentioned for a field, return "Not mentioned" for strings or [] for lists
- Include today's date (2025-11-16) for measurements taken during this consultation
- Extract disease names, chronic conditions into diagnoses

OUTPUT (JSON ONLY - no markdown):
{{
{',\n'.join([f'    "{field}": "<extract or \'Not mentioned\'>"' for field in fields_to_extract])}
}}
"""
        
        logger.info("Sending request to Gemini AI...")
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith('```'):
            response_text = response_text[3:]  # Remove ```
        if response_text.endswith('```'):
            response_text = response_text[:-3]  # Remove ```
        
        response_text = response_text.strip()
        
        # Parse JSON response
        extracted_data = json.loads(response_text)
        
        logger.info("✓ Successfully extracted information using Gemini AI")
        logger.info(f"🔍 Gemini raw response: {extracted_data}")
        
        # Clean up "Not mentioned" values and validate data types
        for key, value in list(extracted_data.items()):
            if isinstance(value, str):
                if value.lower() == "not mentioned" or value.strip() == "":
                    # Check if this should be a list field
                    if key in ['vital_signs', 'clinical_notes', 'diagnoses', 'medications', 
                              'procedures', 'immunizations', 'lab_results']:
                        extracted_data[key] = []
                    else:
                        extracted_data[key] = ""
            elif isinstance(value, list) and len(value) == 0:
                extracted_data[key] = []
        
        logger.info(f"📋 After cleanup: {extracted_data}")
        return extracted_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        logger.error(f"Response text: {response_text}")
        return {}
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return {}


def save_ehr_to_json(ehr_data, output_path):
    """
    Saves the EHR data to a JSON file.
    
    Args:
        ehr_data (dict): The EHR data to save
        output_path (str): Path where the JSON file will be saved
    
    Returns:
        bool: True if save was successful, False otherwise
    """
    
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to JSON file with pretty formatting
        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(ehr_data, json_file, indent=4, ensure_ascii=False)
        
        logger.info(f"✓ EHR data saved to: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving EHR data: {e}")
        return False


def extract_clinical_data(transcript_text):
    """
    Convenience wrapper to extract clinical entities from raw transcript text.

    Returns a dict containing clinical fields suitable for inclusion in the
    patient's EHR (lists for structured fields, strings for simple text fields).
    """
    try:
        fields = [
            'symptoms', 'diagnoses', 'medications', 'vital_signs', 'clinical_notes',
            'allergies_mentioned', 'procedures', 'immunizations', 'lab_results',
            'lifestyle_notes'
        ]
        extracted = extract_with_gemini(transcript_text, fields)

        # Ensure expected keys exist with sensible defaults
        clinical = {}
        for f in fields:
            if f in extracted:
                clinical[f] = extracted[f]
            else:
                clinical[f] = [] if f in ['diagnoses', 'medications', 'vital_signs', 'clinical_notes', 'procedures', 'immunizations', 'lab_results'] else ''

        return clinical
    except Exception as e:
        logger.error(f"Error extracting clinical data: {e}")
        return {}


# Example usage for testing
if __name__ == "__main__":
    # Example EHR template
    patient_ehr_template = {
        "patient_id": "PAT001",
        "patient_name": "John Doe",
        "patient_age": 45,
        "symptoms": "",
        "allergies_mentioned": "",
        "lifestyle_notes": ""
    }
    
    # Example transcript path (you would get this from Module 1)
    transcript_path = "../data/sessions/PAT001_20251115_120000/PAT001_transcript_20251115_120000.json"
    
    if os.path.exists(transcript_path):
        # Fill the EHR
        updated_ehr = autofill_ehr(transcript_path, patient_ehr_template)
        
        if updated_ehr:
            print("\n✓ Updated EHR Profile:")
            print(json.dumps(updated_ehr, indent=2))
            
            # Save to file
            output_path = "../data/sessions/PAT001_20251115_120000/ehr_PAT001.json"
            save_ehr_to_json(updated_ehr, output_path)
    else:
        print(f"Transcript file not found: {transcript_path}")
        print("\nTo test this module:")
        print("1. Run Module 1 (transcription_engine.py) first to create a transcript")
        print("2. Then run this module to auto-fill the EHR")
