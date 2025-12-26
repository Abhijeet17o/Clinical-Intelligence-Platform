import sqlite3

DB_PATH = 'pharmacy.db'

UPDATES = {
    "Paracetamol": "Analgesic and antipyretic agent used for the relief of mild to moderate pain, headache, fever, chills, and body ache.",
    "Paracetamol 500mg": "Analgesic and antipyretic agent used for the relief of mild to moderate pain, headache, fever, chills, and body ache.",
    "Metformin": "Biguanide medication used to treat type 2 diabetes, high blood sugar, excessive thirst, and fatigue.",
}

def update():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count = 0
    for name, desc in UPDATES.items():
        cursor.execute("UPDATE medicines SET description = ? WHERE name LIKE ?", (desc, f"%{name}%"))
        count += cursor.rowcount
        
    conn.commit()
    conn.close()
    print(f"Updated {count} descriptions.")

if __name__ == "__main__":
    update()
