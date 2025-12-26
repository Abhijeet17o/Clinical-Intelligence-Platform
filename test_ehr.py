"""
Test script to verify EHR system database changes
"""

import json
from modules.database_module import MedicineDatabase

# Test database connection
print("="*70)
print("Testing EHR System Database Updates")
print("="*70)

try:
    # Connect to database
    db = MedicineDatabase('pharmacy.db')
    print("\n✓ Database connection successful")
    
    # Test getting all patients
    patients = db.get_all_patients()
    print(f"\n✓ Retrieved {len(patients)} patients")
    
    if patients:
        # Show first patient
        patient = patients[0]
        print(f"\nFirst patient: {patient['full_name']}")
        print(f"  - Patient ID: {patient['patient_id']}")
        print(f"  - DOB: {patient.get('date_of_birth', 'Not set')}")
        print(f"  - Gender: {patient.get('gender', 'Not set')}")
        print(f"  - Insurance: {patient.get('insurance_info', 'Not set')}")
        
        # Parse EHR data
        ehr_data = json.loads(patient['ehr_data']) if patient['ehr_data'] else {}
        print(f"\nEHR Data Structure:")
        for section in ehr_data.keys():
            count = len(ehr_data[section]) if isinstance(ehr_data[section], list) else 'N/A'
            print(f"  - {section}: {count} entries")
    
    print("\n" + "="*70)
    print("✅ All tests passed!")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'db' in locals():
        db.close_connection()
