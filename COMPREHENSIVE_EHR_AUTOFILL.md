# Comprehensive EHR Autofill Feature

## Overview
The EHR system now uses AI (Gemini 2.5 Flash) to automatically extract and populate **all EHR fields** from consultation transcripts while preserving existing data.

## Key Features

### ✅ Smart Field Preservation
- **Rule**: Only fills empty/null fields
- **Protection**: Existing data is NEVER overwritten
- **Validation**: Checks both string and list fields before updating

### 📋 Comprehensive Extraction

#### Demographics (Patient Table)
Automatically extracted and stored in `patients` table:
- **Gender**: Male/Female/Other
- **Insurance Info**: Provider name, policy details

#### Medical Data (EHR JSON)
Automatically extracted and stored in `ehr_data` JSON field:

1. **Vital Signs** (Array)
   - Height, Weight, BMI
   - Blood Pressure
   - Pulse Rate
   - Temperature
   - Respiratory Rate
   - Date, Value, Unit for each measurement

2. **Clinical Notes** (Array)
   - Doctor observations
   - Physical examination findings
   - Assessment notes
   - Date, Provider, Note text

3. **Symptoms** (String)
   - Patient complaints
   - Current conditions
   - Subjective findings

4. **Diagnoses** (Array)
   - Condition name
   - ICD code (if mentioned)
   - Date diagnosed
   - Status (active/resolved)

5. **Medications** (Array)
   - Medicine name
   - Dosage
   - Frequency
   - Start date
   - Route of administration

6. **Allergies** (String)
   - Drug allergies
   - Food allergies
   - Environmental allergies

7. **Procedures** (Array)
   - Procedure name
   - Date performed
   - Provider
   - Notes

8. **Immunizations** (Array)
   - Vaccine name
   - Date administered
   - Provider
   - Lot number

9. **Lab Results** (Array)
   - Test name
   - Value
   - Unit
   - Reference range
   - Abnormal flag
   - Date

10. **Lifestyle Notes** (String)
    - Occupation
    - Exercise habits
    - Diet
    - Smoking/Alcohol use
    - Sleep patterns

## How It Works

### Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Record Consultation → Audio File (.wav)                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Transcribe Audio → JSON Transcript (Whisper AI)         │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Identify Empty Fields in Patient EHR                    │
│    - Check patient table: gender, insurance_info           │
│    - Check ehr_data JSON: all 8 sections                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Extract with Gemini AI (Only Empty Fields)              │
│    - Send transcript + field descriptions                  │
│    - Receive structured JSON response                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Update Database (Two-Tier Strategy)                     │
│    ├─ Patient Table: gender, insurance_info                │
│    └─ EHR JSON: vital_signs, diagnoses, medications, etc.  │
└─────────────────────────────────────────────────────────────┘
```

### Code Flow

**File: `app.py` → `process_consultation()`**
```python
# Step 1: Transcribe audio
transcript_path = transcription_engine.transcribe_conversation(...)

# Step 2: Extract comprehensive medical data
updated_ehr_data = ehr_autofill.autofill_ehr(transcript_path, current_ehr_data)

# Step 3: Extract demographics (if empty)
if not patient['gender'] or not patient['insurance_info']:
    demographics = ehr_autofill.extract_with_gemini(
        transcript_text, 
        ['gender', 'insurance_info']
    )
    # Update patient table
    db.update_patient_info(patient_id, gender=..., insurance_info=...)

# Step 4: Save EHR data
db.update_patient_ehr(patient_id, updated_ehr_data)
```

**File: `modules/ehr_autofill.py` → `autofill_ehr()`**
```python
# Find empty fields
empty_fields = [field for field, value in ehr_data.items() 
                if not value or value == "" or value == []]

# Extract only empty fields
extracted_data = extract_with_gemini(transcript_text, empty_fields)

# Update only if still empty (double-check)
for field, value in extracted_data.items():
    if is_field_empty(ehr_data[field]) and value:
        ehr_data[field] = value  # ✅ Update
    else:
        pass  # ❌ Skip (already filled)
```

## Example Scenarios

### Scenario 1: New Patient - First Consultation
**Transcript**: "I'm John, 45-year-old male. I have diabetes and high blood pressure. Taking metformin 500mg twice daily."

**Extracted Data**:
```json
{
  "demographics": {
    "gender": "Male"
  },
  "ehr_data": {
    "diagnoses": [
      {"condition": "Diabetes Mellitus Type 2", "date": "2025-11-16"},
      {"condition": "Hypertension", "date": "2025-11-16"}
    ],
    "medications": [
      {"name": "Metformin", "dosage": "500mg", "frequency": "Twice daily", "start_date": "2025-11-16"}
    ]
  }
}
```

### Scenario 2: Follow-up - Partial Data Exists
**Existing Data**:
```json
{
  "gender": "Male",  // ✅ Already filled
  "diagnoses": [{"condition": "Diabetes", "date": "2025-01-15"}],  // ✅ Already filled
  "medications": []  // ❌ Empty
}
```

**Transcript**: "I'm taking aspirin 75mg daily now. My blood pressure was 130/85 today."

**Result**:
- Gender: NOT updated (already "Male")
- Diagnoses: NOT updated (already has diabetes)
- Medications: ✅ UPDATED with aspirin
- Vital Signs: ✅ ADDED blood pressure measurement

### Scenario 3: Comprehensive Initial Assessment
**Transcript**: "I'm Sarah, female, 32 years old. I work as a software engineer. I have health insurance with Blue Cross. I've been experiencing headaches for the past week. No known allergies. I exercise 3 times a week. My blood pressure today is 118/76, pulse 72."

**Extracted**:
- Gender: Female ✅
- Insurance: Blue Cross ✅
- Symptoms: "Headaches for the past week" ✅
- Allergies: "No known allergies" ✅
- Lifestyle: "Software engineer, exercises 3 times a week" ✅
- Vital Signs: [BP: 118/76, Pulse: 72] ✅

## Database Structure

### Patients Table
```sql
CREATE TABLE patients (
    patient_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    date_of_birth TEXT,
    contact_info TEXT,
    gender TEXT,              -- ✅ Auto-filled from transcript
    insurance_info TEXT,      -- ✅ Auto-filled from transcript
    ehr_data TEXT NOT NULL    -- JSON containing medical data
)
```

### EHR Data JSON Structure
```json
{
  "vital_signs": [
    {
      "date": "2025-11-16",
      "type": "Blood Pressure",
      "value": "120/80",
      "unit": "mmHg"
    }
  ],
  "clinical_notes": [
    {
      "date": "2025-11-16",
      "provider": "Dr. Smith",
      "note": "Patient appears healthy, no acute distress"
    }
  ],
  "symptoms": "Headache, fatigue for 3 days",
  "diagnoses": [
    {
      "date": "2025-11-16",
      "condition": "Migraine",
      "icd_code": "G43.909"
    }
  ],
  "medications": [
    {
      "name": "Ibuprofen",
      "dosage": "400mg",
      "frequency": "Three times daily",
      "start_date": "2025-11-16"
    }
  ],
  "allergies_mentioned": "Penicillin allergy (anaphylaxis)",
  "procedures": [
    {
      "date": "2025-10-15",
      "procedure": "Blood test",
      "notes": "Routine annual checkup"
    }
  ],
  "immunizations": [
    {
      "vaccine": "COVID-19 Booster",
      "date": "2025-09-01",
      "provider": "City Clinic"
    }
  ],
  "lab_results": [
    {
      "test_name": "HbA1c",
      "value": "5.7",
      "unit": "%",
      "reference_range": "4.0-5.6",
      "date": "2025-10-15",
      "abnormal_flag": true
    }
  ],
  "lifestyle_notes": "Non-smoker, occasional alcohol, regular exercise"
}
```

## AI Prompt Engineering

### Gemini Extraction Prompt Template
```
You are an expert medical information extraction AI.

TRANSCRIPT:
"[Full conversation text]"

FIELDS TO EXTRACT:
- vital_signs: List of measurements (BP, pulse, temp, etc.)
- clinical_notes: Doctor observations
- symptoms: Patient complaints
- diagnoses: Identified conditions
- medications: Current medicines
- allergies_mentioned: Known allergies
- procedures: Medical procedures
- immunizations: Vaccination history
- lab_results: Test results
- lifestyle_notes: Habits, occupation
- gender: Male/Female/Other
- insurance_info: Insurance details

GUIDELINES:
1. Extract EVERYTHING medically relevant
2. Format lists as JSON arrays
3. Format strings as plain text
4. Use today's date for current consultation
5. Return "Not mentioned" or [] if nothing found

OUTPUT (JSON ONLY):
{
  "vital_signs": [...],
  "symptoms": "...",
  ...
}
```

## Testing Instructions

### Test Case 1: Gender Extraction
1. Create new patient (no gender set)
2. Record consultation saying "I'm a male patient"
3. Submit consultation
4. **Expected**: Patient table `gender` = "Male"

### Test Case 2: Vital Signs Extraction
1. Select patient with empty vital_signs
2. Record: "My blood pressure is 120/80 and pulse is 72"
3. **Expected**: `vital_signs` array has 2 entries (BP and pulse)

### Test Case 3: Data Preservation
1. Patient already has `gender = "Female"`
2. Record: "I'm male" (incorrect statement)
3. **Expected**: Gender remains "Female" (NOT overwritten)

### Test Case 4: Comprehensive First Visit
1. New patient
2. Record full consultation with demographics, symptoms, vitals, allergies
3. **Expected**: All mentioned fields populated, empty fields remain empty

## Benefits

✅ **Automatic**: No manual data entry required
✅ **Intelligent**: AI understands medical context
✅ **Safe**: Preserves existing data
✅ **Comprehensive**: Covers all EHR sections
✅ **Structured**: Consistent JSON format
✅ **Scalable**: Works for any consultation length

## Limitations

⚠️ **AI Accuracy**: Gemini may misinterpret complex medical terms
⚠️ **Date Assumptions**: Uses current date for unstated measurements
⚠️ **Language**: Optimized for English transcripts
⚠️ **Empty = Null**: Distinguishes empty from "Not mentioned"

## Future Enhancements

🔮 **Planned Features**:
- Confidence scores for each extraction
- Multi-language support
- Medical terminology validation
- Duplicate detection (e.g., same diagnosis mentioned twice)
- Historical data comparison
- Automatic ICD code lookup
- Lab result trend analysis

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-16  
**Module**: `modules/ehr_autofill.py`  
**Integration**: `app.py` → `process_consultation()`
