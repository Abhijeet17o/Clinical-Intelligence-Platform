import sqlite3
import json
import os
import sys

# Add root to path
sys.path.append(os.getcwd())

from modules.recommenders.knowledge_recommender import KnowledgeRecommender

def inspect():
    # 1. Dump Medicines
    print("--- MEDICINES IN DB ---")
    conn = sqlite3.connect('pharmacy.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, stock_level FROM medicines")
    medicines = []
    print(f"Total medicines: {len(cursor.fetchall())}")
    # Reset cursor
    cursor.execute("SELECT name, description, stock_level FROM medicines")
    
    count = 0
    for row in cursor.fetchall():
        med = {'name': row[0], 'description': row[1], 'stock_level': row[2]}
        medicines.append(med)
        if count < 5:
            print(f"{med['name']}: {med['description']}")
        count += 1
    conn.close()

    # 2. Find latest transcript
    sessions_dir = os.path.join('data', 'sessions')
    if not os.path.exists(sessions_dir):
        print("No sessions dir")
        return

    # Find latest directory
    all_sessions = [os.path.join(sessions_dir, d) for d in os.listdir(sessions_dir) if os.path.isdir(os.path.join(sessions_dir, d))]
    if not all_sessions:
        print("No sessions found")
        return
        
    latest_session = max(all_sessions, key=os.path.getmtime)
    print(f"\n--- LATEST SESSION: {latest_session} ---")

    transcript_path = os.path.join(latest_session, 'transcripts')
    # Find json file in transcripts
    transcript_file = None
    if os.path.exists(transcript_path):
        files = [f for f in os.listdir(transcript_path) if f.endswith('.json')]
        if files:
            transcript_file = os.path.join(transcript_path, files[0])
    
    if transcript_file:
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                text = data.get('transcript', '')
                print(f"TRANSCRIPT TEXT: '{text}'")

            # 3. Test Knowledge Recommender
            kr = KnowledgeRecommender()
            print("\n--- KNOWLEDGE RECOMMENDER DEBUG ---")
            symptoms = kr._extract_symptoms(text)
            print(f"Detected Symptoms: {symptoms}")
            
            if symptoms:
                match_keywords = set()
                for s in symptoms:
                    match_keywords.update(kr.rules.get(s, set()))
                print(f"Looking for keywords: {match_keywords}")
                
                scores = kr.recommend(text, medicines)
                
                # Show non-zero
                print("\nNon-zero matches:")
                found_any = False
                for i, score in enumerate(scores):
                    if score > 0:
                        print(f"  {medicines[i]['name']} -> {score}")
                        found_any = True
                if not found_any:
                    print("  None.")
            else:
                print("No symptoms detected by rules.")
        except Exception as e:
            print(f"Error reading transcript: {e}")
                
    else:
        print("No transcript file found.")

if __name__ == "__main__":
    inspect()
