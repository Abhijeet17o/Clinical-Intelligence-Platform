import sqlite3
import json
import random
import uuid
import datetime

# --- CONFIGURATION ---
DB_PATH = 'pharmacy.db'
NUM_PATIENTS = 200

# --- RICH MEDICINE DESCRIPTIONS (For TF-IDF/Semantic) ---
MEDICINE_UPDATES = {
    # Pain & Fever
    "Paracetamol": "Analgesic and antipyretic agent used for the relief of mild to moderate pain, headache, and fever.",
    "Paracetamol 500mg": "Analgesic and antipyretic agent used for the relief of mild to moderate pain, headache, and fever. Standard dosage.",
    "Ibuprofen": "Non-steroidal anti-inflammatory drug (NSAID) used for treating pain, fever, and inflammation including headache, toothache, and back pain.",
    "Ibuprofen 400mg": "Non-steroidal anti-inflammatory drug (NSAID) used for treating pain, fever, and inflammation. Higher strength.",
    "Aspirin 75mg": "Salicylate used to reduce fever and relieve mild to moderate pain. Also used as a blood thinner to prevent heart attacks.",
    "Diclofenac": "NSAID used to treat pain and inflammatory diseases such as arthritis and gout.",
    
    # Antibiotics
    "Amoxicillin": "Penicillin antibiotic used to treat bacterial infections such as pneumonia, bronchitis, ear infections, and skin infections.",
    "Azithromycin": "Macrolide antibiotic used for the treatment of a number of bacterial infections including respiratory infections and ear infections.",
    "Ciprofloxacin": "Fluoroquinolone antibiotic used to treat a variety of bacterial infections.",
    
    # Respiratory
    "Cetirizine 10mg": "Antihistamine used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing.",
    "Loratadine 10mg": "Non-drowsy antihistamine used to treat allergies, hives, and hay fever.",
    "Salbutamol Inhaler": "Bronchodilator (beta-2 agonist) used to relieve symptoms of asthma and COPD such as coughing, wheezing and feeling breathless.",
    "Montelukast": "Leukotriene receptor antagonist used for the maintenance treatment of asthma and to relieve symptoms of seasonal allergies.",
    "Cough Syrup": "Antitussive and expectorant combination for relief of cough and chest congestion.",
    
    # Gastrointestinal
    "Omeprazole": "Proton pump inhibitor (PPI) that decreases the amount of acid produced in the stomach. Used for GERD and acid reflux.",
    "Pantoprazole": "Proton pump inhibitor used for erosive esophagitis and other conditions involving excess stomach acid.",
    "Ranitidine": "H2 blocker that reduces stomach acid. Used to treat and prevent ulcers and acid reflux.",
    "Domperidone": "Antidopaminergic agent used to treat nausea and vomiting, and certain gastrointestinal problems.",
    "Ondansetron": "Antiemetic used to prevent nausea and vomiting.",
    
    # Chronic
    "Metformin": "Biguanide medication used to treat type 2 diabetes by lowering blood sugar levels and improving insulin sensitivity.",
    "Glipizide": "Sulfonylurea class medication used to treat type 2 diabetes by stimulating pancreas to release insulin.",
    "Insulin Glargine": "Long-acting insulin analogue used to treat diabetes mellitus.",
    "Amlodipine": "Calcium channel blocker used to treat high blood pressure (hypertension) and chest pain (angina).",
    "Lisinopril": "ACE inhibitor used to treat high blood pressure and heart failure.",
    "Losartan": "Angiotensin II receptor blocker (ARB) used to treat high blood pressure.",
    "Atorvastatin": "Statin medication used to lower cholesterol levels and reduce risk of heart disease.",
    
    # Mental Health
    "Alprazolam": "Benzodiazepine used for the management of anxiety disorders and panic disorders.",
    "Sertraline": "SSRI antidepressant used to treat depression, excessive anxiety, and OCD.",
}

# --- SCENARIOS (For Collaborative Filtering) ---
SCENARIOS = [
    {
        "name": "Viral Fever",
        "symptoms": ["fever", "headache", "body pain", "weakness", "chills"],
        "medicines": ["Paracetamol 500mg", "Ibuprofen 400mg"]
    },
    {
        "name": "Common Cold/Allergy",
        "symptoms": ["runny nose", "sneezing", "watery eyes", "itching", "congestion"],
        "medicines": ["Cetirizine 10mg", "Montelukast"]
    },
    {
        "name": "Bacterial Infection",
        "symptoms": ["high fever", "sore throat", "cough", "yellow sputum"],
        "medicines": ["Amoxicillin", "Paracetamol"]
    },
    {
        "name": "Acid Reflux/GERD",
        "symptoms": ["heartburn", "acid reflux", "stomach pain", "indigestion", "burning chest"],
        "medicines": ["Omeprazole", "Domperidone"]
    },
    {
        "name": "Hypertension",
        "symptoms": ["high blood pressure", "headache", "dizziness", "palpitations"],
        "medicines": ["Amlodipine", "Lisinopril"]
    },
    {
        "name": "Type 2 Diabetes",
        "symptoms": ["excessive thirst", "frequent urination", "fatigue", "blurred vision"],
        "medicines": ["Metformin", "Glipizide"]
    },
    {
        "name": "Asthma Exacerbation",
        "symptoms": ["wheezing", "shortness of breath", "cough", "chest tightness"],
        "medicines": ["Salbutamol Inhaler", "Montelukast"]
    },
    {
        "name": "Migraine",
        "symptoms": ["severe headache", "nausea", "sensitivity to light", "pulsing pain"],
        "medicines": ["Paracetamol", "Domperidone"]
    },
    {
        "name": "Skin Allergy",
        "symptoms": ["rash", "itching", "redness", "hives"],
        "medicines": ["Loratadine 10mg", "Cetirizine 10mg"]
    },
    {
        "name": "General Body Pain",
        "symptoms": ["back pain", "joint pain", "muscle chill", "stiffness"],
        "medicines": ["Ibuprofen", "Diclofenac"]
    }
]

def generate_patient_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("--- 1. ENRICHING MEDICINE DESCRIPTIONS ---")
    updated_count = 0
    for name, desc in MEDICINE_UPDATES.items():
        # Check if medicine exists
        cursor.execute("SELECT id FROM medicines WHERE name LIKE ?", (f"%{name}%",))
        rows = cursor.fetchall()
        for row in rows:
            med_id = row[0]
            cursor.execute("UPDATE medicines SET description = ? WHERE id = ?", (desc, med_id))
            updated_count += 1
    print(f"Updated {updated_count} medicine descriptions.")
    conn.commit()

    print(f"\n--- 2. GENERATING {NUM_PATIENTS} SYNTHETIC PATIENTS ---")
    
    # Prepare common names
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

    patients_created = 0
    prescriptions_created = 0

    for i in range(NUM_PATIENTS):
        # Generate random patient details
        p_id = f"SYNTH_{uuid.uuid4().hex[:8].upper()}"
        f_name = random.choice(first_names)
        l_name = random.choice(last_names)
        full_name = f"{f_name} {l_name}"
        dob = f"{random.randint(1950, 2005)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        contact = f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        gender = random.choice(["Male", "Female"])
        
        # Pick a Random Scenario
        scenario = random.choice(SCENARIOS)
        
        # Create EHR JSON structure
        # We simulate that the patient ALREADY HAS this history
        prescription_date = (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
        
        # Find exact medicine objects from DB to mimic real structure
        med_objects = []
        for med_name in scenario['medicines']:
             # Simple lookup
             med_objects.append({"name": med_name, "dosage": "Standard", "duration": "5 days"})

        ehr_data = {
            "patient_id": p_id,
            "patient_name": full_name,
            "symptoms": scenario['symptoms'], # Current/Past symptoms
            "prescriptions": [
                {
                    "date": prescription_date,
                    "medicines": med_objects,
                    "symptoms": scenario['symptoms'], # Associated symptoms
                    "diagnosis": scenario['name']
                }
            ],
            "allergies": [],
            "medical_history": [scenario['name']]
        }
        
        ehr_json = json.dumps(ehr_data)

        # Insert Patient
        try:
            cursor.execute('''
                INSERT INTO patients (patient_id, full_name, date_of_birth, contact_info, gender, insurance_provider, ehr_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (p_id, full_name, dob, contact, gender, "DemoHealth", ehr_json))
            patients_created += 1
            prescriptions_created += 1
        except Exception as e:
            print(f"Error creating patient {p_id}: {e}")

    conn.commit()
    conn.close()
    
    print(f"\nSUCCESS: Created {patients_created} patients with {prescriptions_created} prescriptions.")
    print("The system is now 'trained' for demo purposes.")

if __name__ == "__main__":
    generate_patient_data()
