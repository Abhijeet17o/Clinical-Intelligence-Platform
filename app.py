"""
Flask Web Application for EHR System
Main patient dashboard and management interface
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from modules.database_module import MedicineDatabase
# Lazy import for heavy AI modules to speed up startup
# from modules import transcription_engine, ehr_autofill, recommendation_module
import logging
import uuid
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

# Add ffmpeg to PATH if it exists in the project directory
ffmpeg_bin = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'bin')
if os.path.exists(ffmpeg_bin):
    os.environ['PATH'] = ffmpeg_bin + os.pathsep + os.environ['PATH']
    print(f"✅ FFmpeg added to PATH: {ffmpeg_bin}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lazy loading for heavy AI modules
_transcription_engine = None
_ehr_autofill = None
_recommendation_module = None

def get_transcription_engine():
    """Lazy load transcription engine"""
    global _transcription_engine
    if _transcription_engine is None:
        from modules import transcription_engine
        _transcription_engine = transcription_engine
    return _transcription_engine

def get_ehr_autofill():
    """Lazy load EHR autofill module"""
    global _ehr_autofill
    if _ehr_autofill is None:
        from modules import ehr_autofill
        _ehr_autofill = ehr_autofill
    return _ehr_autofill

def get_recommendation_module():
    """Lazy load recommendation module"""
    global _recommendation_module
    if _recommendation_module is None:
        from modules import recommendation_module
        _recommendation_module = recommendation_module
    return _recommendation_module

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'  # Required for flash messages

# Configure file upload settings
UPLOAD_FOLDER = 'data/temp_audio'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'webm', 'm4a'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ensure sessions directory exists
os.makedirs('data/sessions', exist_ok=True)

# Database connection getter (creates new connection per request to avoid threading issues)
def get_db():
    """Get database connection for current request"""
    return MedicineDatabase('pharmacy.db')

print("\n" + "="*70)
print("🏥 EHR WEB APPLICATION - PATIENT MANAGEMENT SYSTEM")
print("="*70)
print("\nStarting Flask server...")
print(f"\n📍 Access the application at: http://127.0.0.1:5000")
print("\nAvailable routes:")
print("  • Patient Dashboard:  http://127.0.0.1:5000/")
print("  • Add New Patient:    http://127.0.0.1:5000/new_patient")
print("  • Pharmacy Manager:   http://127.0.0.1:5000/pharmacy")
print("\n" + "="*70 + "\n")


@app.route('/')
def dashboard():
    """
    Patient Dashboard - Homepage
    
    Displays a list of all registered patients in the system.
    """
    logger.info("Loading patient dashboard")
    
    # Get all patients from database
    patients = get_db().get_all_patients()
    
    logger.info(f"Retrieved {len(patients)} patients")
    
    # Render the dashboard template with patient data
    return render_template('dashboard.html', patients=patients)


@app.route('/new_patient', methods=['GET', 'POST'])
def new_patient():
    """
    Add New Patient - Form and Handler
    
    GET: Display the patient registration form
    POST: Process the form submission and create new patient record
    """
    if request.method == 'POST':
        # Retrieve form data
        full_name = request.form.get('full_name', '').strip()
        date_of_birth = request.form.get('date_of_birth', '').strip()
        contact_info = request.form.get('contact_info', '').strip()
        
        # Validate required fields
        if not full_name:
            flash('Patient name is required!', 'error')
            return redirect(url_for('new_patient'))
        
        # Generate unique patient ID
        # Format: P followed by timestamp and random suffix for uniqueness
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = str(uuid.uuid4())[:4].upper()
        patient_id = f'P{timestamp}{random_suffix}'
        
        # Add patient to database
        success = get_db().add_new_patient(
            patient_id=patient_id,
            full_name=full_name,
            date_of_birth=date_of_birth,
            contact_info=contact_info
        )
        
        if success:
            logger.info(f"Successfully added new patient: {full_name} (ID: {patient_id})")
            flash(f'Patient {full_name} successfully registered with ID: {patient_id}', 'success')
            return redirect(url_for('dashboard'))
        else:
            logger.error(f"Failed to add patient: {full_name}")
            flash('Error adding patient. Please try again.', 'error')
            return redirect(url_for('new_patient'))
    
    # GET request: Display the form
    return render_template('add_patient.html')


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/process_consultation/<patient_id>', methods=['POST'])
def process_consultation(patient_id):
    """
    Process Consultation Recording
    
    Orchestrates the full AI pipeline:
    1. Receives audio file
    2. Transcribes audio to text
    3. Extracts EHR data using AI
    4. Updates patient EHR in database
    5. Generates medicine recommendations
    6. Returns recommendations as JSON
    
    Args:
        patient_id (str): Unique identifier for the patient
    
    Returns:
        JSON response with recommended medicines or error message
    """
    logger.info(f"Processing consultation for patient: {patient_id}")
    
    try:
        # Step 1: Validate and receive audio file
        if 'audio' not in request.files:
            logger.error("No audio file in request")
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            logger.error("Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(audio_file.filename):
            logger.error(f"Invalid file type: {audio_file.filename}")
            return jsonify({'error': 'Invalid file type. Allowed: WAV, MP3, OGG, WebM, M4A'}), 400
        
        # Save audio file temporarily
        filename = secure_filename(f"{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(audio_path)
        logger.info(f"Audio file saved: {audio_path}")
        
        # Create session directory for this consultation
        session_id = f"{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_dir = os.path.join('data', 'sessions', session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Create subdirectories for organized storage
        transcripts_dir = os.path.join(session_dir, 'transcripts')
        os.makedirs(transcripts_dir, exist_ok=True)
        
        logger.info(f"Session directory created: {session_dir}")
        
        # Step 2: Transcribe audio to text
        logger.info("Starting transcription...")
        transcription_engine = get_transcription_engine()
        # Use patient_id and a default doctor_id for web interface
        transcript_path = transcription_engine.transcribe_conversation(
            audio_file_path=audio_path,
            patient_id=patient_id,
            doctor_id="WEB_DOCTOR",  # Default doctor ID for web interface
            output_dir=transcripts_dir  # Specify output directory for transcript
        )
        
        if not transcript_path:
            logger.error("Transcription failed")
            return jsonify({'error': 'Transcription failed. Please check audio quality and try again.'}), 500
        
        logger.info(f"Transcription complete: {transcript_path}")
        
        # Step 3: Get current patient EHR data
        db = get_db()
        patient = db.get_patient(patient_id)
        if not patient:
            logger.error(f"Patient not found: {patient_id}")
            return jsonify({'error': 'Patient not found'}), 404
        
        # Parse EHR data from JSON string to dictionary
        current_ehr_data_str = patient['ehr_data']
        current_ehr_data = json.loads(current_ehr_data_str) if isinstance(current_ehr_data_str, str) else current_ehr_data_str
        logger.info(f"Current EHR data retrieved for patient: {patient_id}")
        
        # Step 4: Extract and update EHR data using AI
        logger.info("Extracting EHR data with AI...")
        ehr_autofill = get_ehr_autofill()
        updated_ehr_data = ehr_autofill.autofill_ehr(transcript_path, current_ehr_data)
        logger.info("EHR extraction complete")
        
        # Step 5: Update patient EHR in database (convert dict back to JSON string)
        updated_ehr_data_str = json.dumps(updated_ehr_data) if isinstance(updated_ehr_data, dict) else updated_ehr_data
        success = db.update_patient_ehr(patient_id, updated_ehr_data_str)
        if success:
            logger.info(f"EHR data updated in database for patient: {patient_id}")
        else:
            logger.warning(f"Failed to update EHR data for patient: {patient_id}")
        
        # Step 6: Get all available medicines from database
        logger.info("Fetching medicine inventory...")
        all_medicines = db.get_all_medicines()
        logger.info(f"Retrieved {len(all_medicines)} medicines from inventory")
        
        # Step 7: Generate AI medicine recommendations
        logger.info("Generating medicine recommendations...")
        recommendation_module = get_recommendation_module()
        recommendations = recommendation_module.get_medicine_recommendations(
            json_transcript_path=transcript_path,
            available_medicines=all_medicines
        )
        logger.info(f"Generated {len(recommendations)} recommendations")
        
        # Step 8: Extract medicine names and similarity scores for response
        recommended_medicines = []
        for rec in recommendations:
            # rec is a tuple: (medicine_name, similarity_score)
            medicine_name, similarity_score = rec
            
            # Find the full medicine details from all_medicines
            medicine_data = next((med for med in all_medicines if med['name'] == medicine_name), None)
            
            if medicine_data:
                recommended_medicines.append({
                    'name': medicine_data['name'],
                    'description': medicine_data['description'],
                    'similarity_score': round(float(similarity_score) * 100, 1),  # Convert to Python float and percentage
                    'stock_level': medicine_data['stock_level']
                })
        
        logger.info(f"✓ Consultation processing complete for patient: {patient_id}")
        
        # Return recommendations as JSON
        return jsonify({
            'success': True,
            'patient_id': patient_id,
            'recommendations': recommended_medicines,
            'transcript_path': transcript_path,
            'message': 'Consultation processed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing consultation: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'An error occurred while processing the consultation'
        }), 500


@app.route('/search_medicine', methods=['POST'])
def search_medicine():
    """
    Search Medicine by Name
    
    Allows doctors to manually search for medicines in the database.
    Returns matching medicines with their details.
    """
    try:
        data = request.get_json()
        search_term = data.get('search_term', '').strip()
        
        if not search_term:
            return jsonify({
                'success': False,
                'error': 'Search term is required'
            }), 400
        
        logger.info(f"Searching for medicine: {search_term}")
        
        db = get_db()
        all_medicines = db.get_all_medicines()
        
        # Filter medicines that match the search term (case-insensitive)
        search_lower = search_term.lower()
        matching_medicines = [
            med for med in all_medicines 
            if search_lower in med['name'].lower() or search_lower in med['description'].lower()
        ]
        
        logger.info(f"Found {len(matching_medicines)} matching medicines")
        
        return jsonify({
            'success': True,
            'medicines': matching_medicines[:10],  # Limit to 10 results
            'count': len(matching_medicines)
        })
        
    except Exception as e:
        logger.error(f"Error searching medicine: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/save_prescription/<patient_id>', methods=['POST'])
def save_prescription(patient_id):
    """
    Save Final Prescription
    
    Saves the finalized prescription to the patient's EHR data.
    Also updates medicine stock levels in the database.
    """
    try:
        data = request.get_json()
        prescription_text = data.get('prescription', '').strip()
        
        if not prescription_text:
            return jsonify({
                'success': False,
                'error': 'Prescription cannot be empty'
            }), 400
        
        logger.info(f"Saving prescription for patient: {patient_id}")
        
        db = get_db()
        
        # Get current patient data
        patient = db.get_patient(patient_id)
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Patient not found'
            }), 404
        
        # Parse current EHR data
        try:
            ehr_data = json.loads(patient['ehr_data']) if patient['ehr_data'] else {}
        except:
            ehr_data = {}
        
        # Add prescription with timestamp
        if 'prescriptions' not in ehr_data:
            ehr_data['prescriptions'] = []
        
        prescription_entry = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'medicines': [line.strip() for line in prescription_text.split('\n') if line.strip()],
            'raw_text': prescription_text
        }
        
        ehr_data['prescriptions'].append(prescription_entry)
        
        # Update patient EHR
        updated_ehr_json = json.dumps(ehr_data, indent=2)
        success = db.update_patient_ehr(patient_id, updated_ehr_json)
        
        if success:
            logger.info(f"Prescription saved successfully for patient: {patient_id}")
            return jsonify({
                'success': True,
                'message': 'Prescription saved successfully',
                'prescription_count': len(ehr_data['prescriptions'])
            })
        else:
            raise Exception("Failed to update patient EHR")
        
    except Exception as e:
        logger.error(f"Error saving prescription: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/get_prescriptions/<patient_id>', methods=['GET'])
def get_prescriptions(patient_id):
    """
    Get Prescription History
    
    Retrieves all past prescriptions for a patient.
    """
    try:
        logger.info(f"Fetching prescriptions for patient: {patient_id}")
        
        db = get_db()
        patient = db.get_patient(patient_id)
        
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Patient not found'
            }), 404
        
        # Parse EHR data
        try:
            ehr_data = json.loads(patient['ehr_data']) if patient['ehr_data'] else {}
        except:
            ehr_data = {}
        
        prescriptions = ehr_data.get('prescriptions', [])
        
        logger.info(f"Found {len(prescriptions)} prescriptions for patient: {patient_id}")
        
        return jsonify({
            'success': True,
            'prescriptions': prescriptions,
            'count': len(prescriptions)
        })
        
    except Exception as e:
        logger.error(f"Error fetching prescriptions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/update_patient/<patient_id>', methods=['POST'])
def update_patient(patient_id):
    """
    Update Patient Information
    
    Updates patient's basic information (name, DOB, contact).
    """
    try:
        data = request.get_json()
        full_name = data.get('full_name', '').strip()
        date_of_birth = data.get('date_of_birth', '').strip()
        contact_info = data.get('contact_info', '').strip()
        
        if not full_name:
            return jsonify({
                'success': False,
                'error': 'Patient name is required'
            }), 400
        
        logger.info(f"Updating patient information: {patient_id}")
        
        db = get_db()
        
        # Get current patient data
        patient = db.get_patient(patient_id)
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Patient not found'
            }), 404
        
        # Update patient using database method (we'll need to add this)
        # For now, we'll manually update via SQL
        conn = db.conn
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE patients 
            SET full_name = ?, date_of_birth = ?, contact_info = ?
            WHERE patient_id = ?
        ''', (full_name, date_of_birth, contact_info, patient_id))
        
        conn.commit()
        
        logger.info(f"Patient information updated successfully: {patient_id}")
        
        return jsonify({
            'success': True,
            'message': 'Patient information updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating patient: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/appointment/<patient_id>')
def appointment(patient_id):
    """
    Patient Appointment Screen
    
    Main consultation interface for a specific patient.
    Displays patient info, EHR data, recording controls, and prescription pad.
    
    Args:
        patient_id (str): Unique identifier for the patient
    """
    logger.info(f"Loading appointment screen for patient: {patient_id}")
    
    # Fetch patient data from database
    patient = get_db().get_patient(patient_id)
    
    if not patient:
        logger.warning(f"Patient not found: {patient_id}")
        flash(f'Patient with ID {patient_id} not found.', 'error')
        return redirect(url_for('dashboard'))
    
    logger.info(f"Loaded appointment for: {patient['full_name']} (ID: {patient_id})")
    
    # Render the appointment template with patient data
    return render_template('appointment.html', patient=patient)


@app.route('/pharmacy')
def pharmacy_management():
    """
    Pharmacy Management - View all medicines
    
    Displays all medicines in the database with their details.
    """
    logger.info("Loading pharmacy management page")
    
    db = get_db()
    medicines = db.get_all_medicines()
    
    logger.info(f"Retrieved {len(medicines)} medicines")
    
    return render_template('pharmacy.html', medicines=medicines)


@app.route('/add_medicine', methods=['POST'])
def add_medicine():
    """Add new medicine to database"""
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        stock_level = int(request.form.get('stock_level', 0))
        
        if not name:
            return jsonify({'success': False, 'error': 'Medicine name is required'}), 400
        
        db = get_db()
        success = db.add_medicine(name, description, stock_level)
        
        if success:
            logger.info(f"Added new medicine: {name}")
            return jsonify({'success': True, 'message': f'Medicine "{name}" added successfully'})
        else:
            return jsonify({'success': False, 'error': 'Medicine already exists or database error'}), 400
            
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid stock level'}), 400
    except Exception as e:
        logger.error(f"Error adding medicine: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/update_medicine/<int:medicine_id>', methods=['POST'])
def update_medicine(medicine_id):
    """Update existing medicine"""
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        stock_level = int(request.form.get('stock_level', 0))
        
        if not name:
            return jsonify({'success': False, 'error': 'Medicine name is required'}), 400
        
        db = get_db()
        cursor = db.connection.cursor()
        
        cursor.execute('''
            UPDATE medicines 
            SET name = ?, description = ?, stock_level = ?
            WHERE id = ?
        ''', (name, description, stock_level, medicine_id))
        
        db.connection.commit()
        
        logger.info(f"Updated medicine ID {medicine_id}: {name}")
        return jsonify({'success': True, 'message': f'Medicine "{name}" updated successfully'})
        
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid stock level'}), 400
    except Exception as e:
        logger.error(f"Error updating medicine: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/delete_medicine/<int:medicine_id>', methods=['POST'])
def delete_medicine(medicine_id):
    """Delete medicine from database"""
    try:
        db = get_db()
        cursor = db.connection.cursor()
        
        # Get medicine name first for logging
        cursor.execute('SELECT name FROM medicines WHERE id = ?', (medicine_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'success': False, 'error': 'Medicine not found'}), 404
        
        medicine_name = result[0]
        
        cursor.execute('DELETE FROM medicines WHERE id = ?', (medicine_id,))
        db.connection.commit()
        
        logger.info(f"Deleted medicine ID {medicine_id}: {medicine_name}")
        return jsonify({'success': True, 'message': f'Medicine "{medicine_name}" deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting medicine: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Cleanup database connection when app shuts down
@app.teardown_appcontext
def close_db(error):
    """Close database connection when application context ends"""
    if error:
        logger.error(f"Application error: {error}")


if __name__ == '__main__':
    import sys
    
    # Check if --no-reload flag is passed
    use_reloader = '--no-reload' not in sys.argv
    
    if not use_reloader:
        print("⚠️  Auto-reload disabled for AI processing")
        sys.argv.remove('--no-reload')
    
    # Run the Flask development server
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=use_reloader)
