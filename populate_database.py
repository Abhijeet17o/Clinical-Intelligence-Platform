"""
Script to populate the medicine database with sample medicines
"""

from modules.database_module import MedicineDatabase

def populate_medicines():
    """Add sample medicines to the database"""
    db = MedicineDatabase('pharmacy.db')
    
    medicines = [
        # Antibiotics
        ("Amoxicillin 500mg", "Antibiotic for bacterial infections", 150, 45),
        ("Azithromycin 250mg", "Macrolide antibiotic for respiratory infections", 80, 30),
        ("Ciprofloxacin 500mg", "Fluoroquinolone antibiotic for various infections", 100, 25),
        ("Doxycycline 100mg", "Tetracycline antibiotic for bacterial infections", 120, 35),
        ("Cephalexin 500mg", "Cephalosporin antibiotic for skin and soft tissue infections", 90, 28),
        
        # Pain Relief & Fever
        ("Ibuprofen 400mg", "NSAID for pain and inflammation", 200, 120),
        ("Paracetamol 500mg", "Analgesic and antipyretic", 300, 200),
        ("Aspirin 75mg", "Antiplatelet and pain relief", 180, 60),
        ("Naproxen 500mg", "NSAID for pain and inflammation", 95, 40),
        ("Diclofenac 50mg", "NSAID for pain and inflammation", 110, 35),
        
        # Diabetes Management
        ("Metformin 500mg", "First-line diabetes medication", 250, 150),
        ("Glimepiride 2mg", "Sulfonylurea for type 2 diabetes", 140, 55),
        ("Insulin Glargine", "Long-acting insulin", 60, 85),
        ("Sitagliptin 100mg", "DPP-4 inhibitor for diabetes", 75, 42),
        
        # Cardiovascular
        ("Atorvastatin 20mg", "Statin for cholesterol management", 200, 95),
        ("Amlodipine 5mg", "Calcium channel blocker for hypertension", 180, 78),
        ("Losartan 50mg", "ARB for hypertension", 160, 65),
        ("Metoprolol 50mg", "Beta-blocker for heart conditions", 140, 58),
        ("Aspirin 325mg", "Antiplatelet for cardiovascular protection", 220, 90),
        
        # Respiratory
        ("Salbutamol Inhaler", "Bronchodilator for asthma", 85, 110),
        ("Montelukast 10mg", "Leukotriene receptor antagonist for asthma", 95, 48),
        ("Cetirizine 10mg", "Antihistamine for allergies", 150, 75),
        ("Loratadine 10mg", "Non-sedating antihistamine", 130, 60),
        ("Prednisolone 5mg", "Corticosteroid for inflammation", 100, 45),
        
        # Gastrointestinal
        ("Omeprazole 20mg", "Proton pump inhibitor for acid reflux", 180, 95),
        ("Pantoprazole 40mg", "PPI for gastric acid reduction", 160, 72),
        ("Ranitidine 150mg", "H2 blocker for acid reduction", 140, 55),
        ("Ondansetron 4mg", "Antiemetic for nausea", 90, 65),
        ("Loperamide 2mg", "Antidiarrheal medication", 110, 38),
        
        # Vitamins & Supplements
        ("Vitamin D3 1000IU", "Vitamin D supplement", 200, 85),
        ("Calcium Carbonate 500mg", "Calcium supplement", 180, 70),
        ("Multivitamin", "Daily vitamin supplement", 150, 90),
        ("Folic Acid 5mg", "Vitamin B9 supplement", 140, 55),
        ("Iron Sulfate 200mg", "Iron supplement for anemia", 120, 48),
        
        # Mental Health
        ("Escitalopram 10mg", "SSRI antidepressant", 85, 62),
        ("Sertraline 50mg", "SSRI for depression and anxiety", 90, 58),
        ("Alprazolam 0.5mg", "Benzodiazepine for anxiety", 70, 45),
        ("Zolpidem 10mg", "Sedative for insomnia", 65, 52),
        
        # Antibacterial/Antifungal
        ("Fluconazole 150mg", "Antifungal medication", 80, 35),
        ("Clotrimazole Cream", "Topical antifungal", 100, 42),
        ("Mupirocin Ointment", "Topical antibiotic", 90, 38),
        
        # Others
        ("Levothyroxine 100mcg", "Thyroid hormone replacement", 150, 78),
        ("Warfarin 5mg", "Anticoagulant", 95, 55),
        ("Allopurinol 300mg", "Uric acid reducer for gout", 110, 42),
        ("Gabapentin 300mg", "Anticonvulsant for nerve pain", 100, 48),
        ("Tramadol 50mg", "Opioid analgesic for moderate pain", 85, 65),
        ("Prednisone 10mg", "Corticosteroid", 120, 52),
        ("Hydrochlorothiazide 25mg", "Diuretic for hypertension", 140, 60),
        ("Lisinopril 10mg", "ACE inhibitor for hypertension", 155, 70),
        ("Simvastatin 40mg", "Statin for cholesterol", 145, 58),
    ]
    
    print("Adding medicines to database...")
    added_count = 0
    for name, desc, stock, freq in medicines:
        success = db.add_medicine(name, desc, stock)
        if success:
            added_count += 1
    
    print(f"\n✅ Successfully added {added_count} medicines to the database!")
    print(f"📊 Total medicines in database: {len(db.get_all_medicines())}")

if __name__ == "__main__":
    populate_medicines()
