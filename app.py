"""
Module 6: Prescription Finalizer - Flask Web Application

A web interface for doctors to review AI-recommended medicines
and finalize prescriptions for patients.
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json
import logging
from datetime import datetime

# Import only database module initially (lazy load recommendation module)
from modules.database_module import MedicineDatabase
from load_env import load_env

# Load environment variables
load_env()

# Lazy import for recommendation module (to avoid slow TensorFlow startup)
_recommendation_module = None

def get_recommendations_module():
    """Lazy load the recommendation module to speed up Flask startup"""
    global _recommendation_module
    if _recommendation_module is None:
        from modules import recommendation_module
        _recommendation_module = recommendation_module
    return _recommendation_module

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'

# Initialize database connection (will be used across routes)
db = None


def get_db():
    """Get database connection (singleton pattern)"""
    global db
    if db is None:
        db = MedicineDatabase('pharmacy.db')
    return db


@app.route('/')
def index():
    """Home page - list all available sessions"""
    sessions_dir = 'data/sessions'
    
    if not os.path.exists(sessions_dir):
        return render_template('index.html', sessions=[])
    
    # Get all session directories
    sessions = []
    for session_id in os.listdir(sessions_dir):
        session_path = os.path.join(sessions_dir, session_id)
        
        if os.path.isdir(session_path):
            # Read session metadata
            metadata_file = os.path.join(session_path, 'session_metadata.json')
            
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Find transcript file
                transcript_file = None
                for file in os.listdir(session_path):
                    if file.endswith('.json') and file.startswith(metadata['patient_id']) and 'transcript' in file.lower():
                        transcript_file = file
                        break
                
                if not transcript_file:
                    # Try alternative naming
                    for file in os.listdir(session_path):
                        if file.endswith('.json') and file != 'session_metadata.json' and file != f"ehr_{metadata['patient_id']}.json":
                            transcript_file = file
                            break
                
                sessions.append({
                    'session_id': session_id,
                    'patient_id': metadata.get('patient_id', 'Unknown'),
                    'patient_name': metadata.get('patient_name', 'Unknown'),
                    'timestamp': metadata.get('created_at', session_id.split('_', 1)[-1] if '_' in session_id else 'Unknown'),
                    'transcript_file': transcript_file
                })
    
    # Sort by timestamp (newest first)
    sessions.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('index.html', sessions=sessions)


@app.route('/prescription')
def prescription():
    """
    Main prescription page - displays recommendations and allows finalization.
    
    Query parameters:
        file: Path to the transcript JSON file (e.g., data/sessions/PAT001_.../PAT001_transcript.json)
    """
    
    # Get the transcript file path from query parameter
    transcript_file = request.args.get('file')
    
    if not transcript_file:
        return "Error: No transcript file specified. Please provide ?file=path/to/transcript.json", 400
    
    # Validate file exists
    if not os.path.exists(transcript_file):
        return f"Error: Transcript file not found: {transcript_file}", 404
    
    try:
        # Read transcript data
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        # Get session ID from file path
        session_id = transcript_file.split('sessions/')[1].split('/')[0]
        session_dir = os.path.join('data/sessions', session_id)
        
        # Read session metadata
        metadata_file = os.path.join(session_dir, 'session_metadata.json')
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Read EHR data
        ehr_file = os.path.join(session_dir, f"ehr_{metadata['patient_id']}.json")
        ehr_data = None
        if os.path.exists(ehr_file):
            with open(ehr_file, 'r') as f:
                ehr_data = json.load(f)
        
        # Get all available medicines from database
        database = get_db()
        available_medicines = database.get_all_medicines()
        
        # Get AI recommendations
        logger.info(f"Generating recommendations for: {transcript_file}")
        rec_module = get_recommendations_module()
        recommendations = rec_module.get_medicine_recommendations(
            transcript_file,
            available_medicines,
            top_n=5
        )
        
        # Format recommendations with full medicine details
        recommendations_with_details = []
        medicine_lookup = {med['name']: med for med in available_medicines}
        
        for medicine_name, similarity_score in recommendations:
            med = medicine_lookup.get(medicine_name)
            if med:
                recommendations_with_details.append({
                    'name': medicine_name,
                    'description': med['description'],
                    'stock_level': med['stock_level'],
                    'prescription_frequency': med['prescription_frequency'],
                    'similarity_score': similarity_score * 100,  # Convert to percentage
                    'low_stock': med['stock_level'] < 10
                })
        
        # Render the prescription page
        return render_template(
            'prescription.html',
            session_id=session_id,
            patient_id=metadata['patient_id'],
            patient_name=metadata['patient_name'],
            patient_age=metadata.get('age', 'N/A'),
            doctor_id=metadata['doctor_id'],
            transcript=transcript_data['transcript'],
            timestamp=transcript_data['conversation_timestamp'],
            ehr_data=ehr_data,
            recommendations=recommendations_with_details,
            all_medicines=available_medicines
        )
        
    except Exception as e:
        logger.error(f"Error processing prescription: {e}", exc_info=True)
        return f"Error processing prescription: {str(e)}", 500


@app.route('/finalize_prescription', methods=['POST'])
def finalize_prescription():
    """
    Finalize the prescription with doctor-selected medicines.
    """
    
    try:
        # Get form data
        session_id = request.form.get('session_id')
        patient_id = request.form.get('patient_id')
        selected_medicines = request.form.getlist('medicines[]')  # List of selected medicine names
        quantities = request.form.getlist('quantities[]')  # Corresponding quantities
        notes = request.form.get('notes', '')
        
        if not selected_medicines:
            return jsonify({'error': 'No medicines selected'}), 400
        
        # Create prescription data
        prescription = {
            'session_id': session_id,
            'patient_id': patient_id,
            'doctor_id': request.form.get('doctor_id'),
            'timestamp': datetime.now().isoformat(),
            'medicines': [],
            'notes': notes
        }
        
        # Get database connection
        database = get_db()
        
        # Process each selected medicine
        for i, medicine_name in enumerate(selected_medicines):
            quantity = int(quantities[i]) if i < len(quantities) else 1
            
            # Get medicine details
            medicine = database.get_medicine_by_name(medicine_name)
            
            if medicine:
                # Add to prescription
                prescription['medicines'].append({
                    'name': medicine_name,
                    'description': medicine['description'],
                    'quantity': quantity
                })
                
                # Update stock
                database.update_stock(medicine_name, -quantity)
                
                # Increment prescription frequency
                database.increment_prescription_frequency(medicine_name)
        
        # Save prescription to session directory
        session_dir = os.path.join('data/sessions', session_id)
        prescription_file = os.path.join(session_dir, f'prescription_{patient_id}.json')
        
        with open(prescription_file, 'w', encoding='utf-8') as f:
            json.dump(prescription, f, indent=4, ensure_ascii=False)
        
        logger.info(f"✓ Prescription finalized for patient {patient_id}")
        
        return jsonify({
            'success': True,
            'message': 'Prescription finalized successfully!',
            'prescription_file': prescription_file,
            'medicines_count': len(selected_medicines)
        })
        
    except Exception as e:
        logger.error(f"Error finalizing prescription: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/inventory')
def inventory():
    """View and manage medicine inventory"""
    
    database = get_db()
    all_medicines = database.get_all_medicines()
    low_stock_medicines = database.get_low_stock_medicines(threshold=10)
    
    return render_template(
        'inventory.html',
        medicines=all_medicines,
        low_stock_count=len(low_stock_medicines)
    )


@app.route('/api/medicines')
def api_medicines():
    """API endpoint to get all medicines (for AJAX calls)"""
    database = get_db()
    medicines = database.get_all_medicines()
    return jsonify(medicines)


# Cleanup on shutdown
@app.teardown_appcontext
def close_db(error):
    """Close database connection when app context ends"""
    global db
    if db is not None:
        db.close_connection()
        db = None


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🏥 PRESCRIPTION FINALIZER - FLASK WEB APPLICATION")
    print("="*70 + "\n")
    print("Starting Flask server...")
    print("\n📍 Access the application at: http://127.0.0.1:5000")
    print("\nAvailable routes:")
    print("  • Home page:        http://127.0.0.1:5000/")
    print("  • Prescription:     http://127.0.0.1:5000/prescription?file=<path>")
    print("  • Inventory:        http://127.0.0.1:5000/inventory")
    print("\n" + "="*70 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
