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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# New lazy loaders for enhanced modules
_ensemble_recommender = None
_xai_engine = None
_fl_simulator = None
_fl_server_manager = None
_fl_client_manager = None
_incremental_learner = None
_learning_history = None

# Consultation context cache: stores symptoms and recommendations per patient
# Format: {patient_id: {'symptoms': str, 'recommendations': List[str], 'timestamp': datetime}}
_consultation_context = {}

# Auto aggregator for federated weight updates
_auto_aggregator = None

def get_auto_aggregator():
    """Lazy load auto aggregator"""
    global _auto_aggregator
    if _auto_aggregator is None:
        from modules.federated.auto_aggregator import AutoAggregator
        _auto_aggregator = AutoAggregator(
            aggregation_interval=300,  # 5 minutes
            min_updates_before_aggregate=5,
            enabled=True
        )
        # Start the aggregator
        _auto_aggregator.start()
    return _auto_aggregator

def get_ensemble_recommender():
    """Lazy load ensemble recommendation engine with hybrid models"""
    global _ensemble_recommender
    if _ensemble_recommender is None:
        from modules.ensemble_engine import EnsembleRecommender
        _ensemble_recommender = EnsembleRecommender(use_learnable_weights=True)
    return _ensemble_recommender

def get_xai_engine():
    """Lazy load explainable AI engine"""
    global _xai_engine
    if _xai_engine is None:
        from modules.explainers import RecommendationExplainer
        _xai_engine = RecommendationExplainer(use_gemini=True)
    return _xai_engine

def get_fl_simulator():
    """Lazy load federated learning simulator"""
    global _fl_simulator
    if _fl_simulator is None:
        from modules.federated import FederatedSimulator
        _fl_simulator = FederatedSimulator()
    return _fl_simulator

def get_fl_server_manager():
    """Lazy load FL server manager for recommender"""
    global _fl_server_manager
    if _fl_server_manager is None:
        from modules.federated.recommender_flower_server import RecommenderFLServerManager
        from modules.federated.fl_config import FLConfig
        config = FLConfig()
        _fl_server_manager = RecommenderFLServerManager(config=config)
    return _fl_server_manager

def get_fl_client_manager():
    """Lazy load FL client manager"""
    global _fl_client_manager
    if _fl_client_manager is None:
        from modules.federated.client_manager import ClientManager
        from modules.federated.fl_config import FLConfig
        config = FLConfig()
        _fl_client_manager = ClientManager(
            deployment_mode=config.deployment_mode,
            heartbeat_timeout=config.heartbeat_timeout,
            max_failures=config.max_client_failures
        )
    return _fl_client_manager

def get_incremental_learner():
    """Lazy load incremental learner"""
    global _incremental_learner
    if _incremental_learner is None:
        from modules.federated.incremental_learner import IncrementalLearner
        ensemble = get_ensemble_recommender()
        _incremental_learner = IncrementalLearner(ensemble=ensemble, learning_rate=0.1)
    return _incremental_learner

def get_learning_history():
    """Lazy load learning history manager"""
    global _learning_history
    if _learning_history is None:
        from modules.federated.learning_history import LearningHistory
        _learning_history = LearningHistory()
    return _learning_history

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
print("  • Patient Dashboard:      http://127.0.0.1:5000/")
print("  • Add New Patient:         http://127.0.0.1:5000/new_patient")
print("  • Pharmacy Manager:        http://127.0.0.1:5000/pharmacy")
print("  • Federated Learning:       http://127.0.0.1:5000/fl_dashboard")
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
        gender = request.form.get('gender', '').strip()
        insurance_info = request.form.get('insurance_info', '').strip()
        
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
            contact_info=contact_info,
            gender=gender,
            insurance_info=insurance_info
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
    """Legacy route - redirecting to new logic internally"""
    return process_consultation_v2(patient_id)

@app.route('/api/process_consultation_v2/<patient_id>', methods=['POST'])
def process_consultation_v2(patient_id):
    """
    Process Consultation - Version 2 (Force New Code)
    """
    try:
        logger.info(f"--- Processing Consultation V2 for {patient_id} ---")
        
        # Check if file part exists
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file part'}), 400
            
        file = request.files['audio']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400
            
        if file and allowed_file(file.filename):
            # Step 1: Save audio file
            filename = f"{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            logger.info(f"Audio saved to: {filepath}")
            
            # Step 2: Transcribe
            logger.info("Transcribing audio...")
            transcription_engine = get_transcription_engine()
            # Note: We pass output_dir to ensure we know where it saves
            transcript_path = transcription_engine.transcribe_conversation(
                filepath, patient_id, "DOC001", output_dir=os.path.join('data', 'sessions', patient_id, 'transcripts')
            )
            
            if not transcript_path:
                logger.error("Transcription failed")
                return jsonify({'success': False, 'error': 'Transcription failed'}), 500
            logger.info(f"Transcription saved to: {transcript_path}")
            
            # Step 3: Read transcript and Update EHR
            # Read transcript
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
            
            # Use correct key 'transcript'
            symptoms_text = transcript_data.get('transcript', '')
            logger.info(f"V2 Transcript length: {len(symptoms_text)}")
            
            if not symptoms_text or len(symptoms_text.strip()) < 2:
                logger.warning("Empty transcript detected")
                return jsonify({
                    'success': False, 
                    'error': 'No speech detected in audio. Please check your microphone and speak clearly.'
                }), 400
            
            # --- Auto-Fill EHR Logic Start ---
            ehr_autofill = get_ehr_autofill()
            db = get_db()
            patient = db.get_patient(patient_id)
            
            if patient:
                # 1. Update demographics if needed
                if not patient.get('gender') or not patient.get('insurance_info'):
                    demographics = ehr_autofill.extract_with_gemini(symptoms_text, ['gender', 'insurance_info'])
                    update_gender = demographics.get('gender', '')
                    update_insurance = demographics.get('insurance_info', '')
                    if update_gender or update_insurance:
                         db.update_patient_info(patient_id, patient['full_name'], patient.get('date_of_birth'), patient.get('contact_info'), update_gender, update_insurance)

                # 2. Extract clinical data using autofill_ehr
                logger.info("Extracting clinical entities...")
                try:
                    current_ehr = json.loads(patient['ehr_data']) if patient.get('ehr_data') else {}
                except:
                    current_ehr = {}
                    
                # Use module's implementation
                updated_ehr = ehr_autofill.autofill_ehr(transcript_path, current_ehr)
                
                # Convert back to string for database
                if isinstance(updated_ehr, dict):
                    updated_ehr_str = json.dumps(updated_ehr)
                else:
                    updated_ehr_str = updated_ehr
                    
                db.update_patient_ehr(patient_id, updated_ehr_str)
            # --- Auto-Fill EHR Logic End ---
            
            # Step 4: Generate HYBRID AI recommendations
            all_medicines = db.get_all_medicines()
            
            ensemble = get_ensemble_recommender()
            ensemble.set_database(db)
            recommendations = ensemble.get_recommendations(symptoms_text, all_medicines, top_n=5)
            
            # Step 5: Add XAI explanations with LIME scoring
            logger.info("Generating XAI explanations...")
            
            # Create a localized scoring function for LIME
            def lime_scorer(s, meds):
                # Use ensemble to get scores for these specific medicines under new symptoms
                res = ensemble.get_recommendations(s, meds)
                # Map back to scores in same order as meds
                scores = []
                for m in meds:
                    score = next((r.get('final_score', 0) for r in res if r['name'] == m['name']), 0)
                    scores.append(float(score))
                return scores

            xai = get_xai_engine()
            explained_recs = xai.explain_batch(symptoms_text, recommendations, recommender_func=lime_scorer)
            
            # Step 6: Format Output
            formatted_recs = []
            for rec in explained_recs:
                formatted_recs.append({
                    'name': rec['name'],
                    'description': rec.get('description', ''),
                    'similarity_score': round(float(rec.get('final_score', 0)) * 100, 1),
                    'final_score': rec.get('final_score', 0),
                    'voting': rec.get('voting', {}),
                    'explanation': rec.get('explanation', {}),
                    'stock_level': rec.get('stock_level', 0)
                })
            
            # Store consultation context for later learning
            recommended_med_names = [rec['name'] for rec in formatted_recs]
            _consultation_context[patient_id] = {
                'symptoms': symptoms_text,
                'recommendations': recommended_med_names,
                'timestamp': datetime.now()
            }
            
            return jsonify({
                'success': True,
                'debug_marker': 'V2_ROUTE_ACTIVE',
                'patient_id': patient_id,
                'recommendations': formatted_recs,
                'transcript_path': transcript_path,
                'weights': ensemble.get_model_weights(),
                'message': 'Consultation processed successfully (V2)'
            }), 200
            
    except Exception as e:
        logger.error(f"Error in V2 processing: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


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
            
            # === INCREMENTAL FEDERATED LEARNING ===
            learning_result = None
            try:
                # Get consultation context (symptoms and recommendations)
                consultation_ctx = _consultation_context.get(patient_id)
                
                if consultation_ctx:
                    symptoms = consultation_ctx.get('symptoms', '')
                    recommended_medicines = consultation_ctx.get('recommendations', [])
                    selected_medicines = prescription_entry['medicines']
                    
                    # Get incremental learner and learning history
                    learner = get_incremental_learner()
                    history = get_learning_history()
                    ensemble = get_ensemble_recommender()
                    all_medicines = db.get_all_medicines()
                    
                    # Learn from each selected medicine
                    for selected_med in selected_medicines:
                        if selected_med:  # Skip empty strings
                            # Trigger learning
                            learning_result = learner.learn_from_prescription(
                                symptoms=symptoms,
                                recommended_medicines=recommended_medicines,
                                selected_medicine=selected_med,
                                all_medicines=all_medicines
                            )
                            
                            if learning_result.get('success'):
                                # Save to learning history
                                history.add_learning_event(
                                    symptoms=symptoms,
                                    recommended_medicines=recommended_medicines,
                                    selected_medicine=selected_med,
                                    learning_result=learning_result
                                )
                                
                                # Add to auto aggregator for federated aggregation
                                try:
                                    aggregator = get_auto_aggregator()
                                    new_weights = learning_result.get('weights_after', {})
                                    aggregator.add_local_update(
                                        weights=new_weights,
                                        metadata={
                                            'medicine': selected_med,
                                            'symptoms': symptoms[:100]
                                        }
                                    )
                                except Exception as e:
                                    logger.warning(f"Error adding to aggregator: {e}")
                                
                                logger.info(
                                    f"✅ Model learned from prescription: "
                                    f"{selected_med} for symptoms: {symptoms[:50]}..."
                                )
                    
                    # Clear consultation context after learning
                    if patient_id in _consultation_context:
                        del _consultation_context[patient_id]
                
                else:
                    logger.warning(
                        f"No consultation context found for patient {patient_id}. "
                        f"Learning skipped. Make sure consultation was processed first."
                    )
            
            except Exception as e:
                logger.error(f"Error in incremental learning: {e}", exc_info=True)
                # Don't fail prescription save if learning fails
                learning_result = {'success': False, 'error': str(e)}
            
            # Return response with learning info
            response_data = {
                'success': True,
                'message': 'Prescription saved successfully',
                'prescription_count': len(ehr_data['prescriptions'])
            }
            
            if learning_result:
                response_data['learning'] = {
                    'success': learning_result.get('success', False),
                    'weights_after': learning_result.get('weights_after', {}),
                    'weight_changes': learning_result.get('weight_changes', {}),
                    'learning_count': learning_result.get('learning_count', 0)
                }
            
            return jsonify(response_data)
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
    
    Updates patient's basic information (name, DOB, contact, gender, insurance).
    """
    try:
        data = request.get_json()
        full_name = data.get('full_name', '').strip()
        date_of_birth = data.get('date_of_birth', '').strip()
        contact_info = data.get('contact_info', '').strip()
        gender = data.get('gender', '').strip()
        insurance_info = data.get('insurance_info', '').strip()
        
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
        
        # Update patient using database method
        success = db.update_patient_info(
            patient_id=patient_id,
            full_name=full_name,
            date_of_birth=date_of_birth,
            contact_info=contact_info,
            gender=gender,
            insurance_info=insurance_info
        )
        
        if success:
            logger.info(f"Patient information updated successfully: {patient_id}")
            return jsonify({
                'success': True,
                'message': 'Patient information updated successfully'
            })
        else:
            raise Exception("Failed to update patient information")
        
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


@app.route('/ehr_report/<patient_id>')
def ehr_report(patient_id):
    """
    Comprehensive EHR Report View
    
    Displays full electronic health record for a patient with all sections.
    
    Args:
        patient_id (str): Unique identifier for the patient
    """
    logger.info(f"Loading EHR report for patient: {patient_id}")
    
    # Fetch patient data from database
    db = get_db()
    patient = db.get_patient(patient_id)
    
    if not patient:
        logger.warning(f"Patient not found: {patient_id}")
        flash(f'Patient with ID {patient_id} not found.', 'error')
        return redirect(url_for('dashboard'))
    
    # Parse EHR data
    try:
        ehr_data = json.loads(patient['ehr_data']) if patient['ehr_data'] else {}
    except:
        ehr_data = {}
    
    # Ensure all sections exist
    if 'vital_signs' not in ehr_data:
        ehr_data['vital_signs'] = []
    if 'clinical_notes' not in ehr_data:
        ehr_data['clinical_notes'] = []
    if 'medications' not in ehr_data:
        ehr_data['medications'] = []
    if 'diagnoses' not in ehr_data:
        ehr_data['diagnoses'] = []
    if 'procedures' not in ehr_data:
        ehr_data['procedures'] = []
    if 'immunizations' not in ehr_data:
        ehr_data['immunizations'] = []
    if 'lab_results' not in ehr_data:
        ehr_data['lab_results'] = []
    if 'prescriptions' not in ehr_data:
        ehr_data['prescriptions'] = []
    
    # Calculate age if date of birth is provided
    age = 'Unknown'
    if patient.get('date_of_birth'):
        try:
            from datetime import datetime
            dob = datetime.strptime(patient['date_of_birth'], '%Y-%m-%d')
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except:
            age = 'Unknown'
    
    logger.info(f"Loaded EHR report for: {patient['full_name']} (ID: {patient_id})")
    
    # Render the EHR report template with patient data
    return render_template('ehr_report.html', patient=patient, ehr_data=ehr_data, age=age)


@app.route('/update_ehr/<patient_id>', methods=['POST'])
def update_ehr(patient_id):
    """
    Update EHR Data
    
    Adds new entries to specific EHR sections.
    """
    try:
        data = request.get_json()
        section = data.get('section')
        entry_data = data.get('data')
        
        if not section or not entry_data:
            return jsonify({
                'success': False,
                'error': 'Section and data are required'
            }), 400
        
        logger.info(f"Updating EHR section '{section}' for patient: {patient_id}")
        
        db = get_db()
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
        
        # Ensure section exists
        if section not in ehr_data:
            ehr_data[section] = []
        
        # Add new entry
        ehr_data[section].append(entry_data)
        
        # Update patient EHR
        updated_ehr_json = json.dumps(ehr_data, indent=2)
        success = db.update_patient_ehr(patient_id, updated_ehr_json)
        
        if success:
            logger.info(f"EHR section '{section}' updated successfully for patient: {patient_id}")
            return jsonify({
                'success': True,
                'message': f'{section} updated successfully'
            })
        else:
            raise Exception("Failed to update patient EHR")
        
    except Exception as e:
        logger.error(f"Error updating EHR: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Cleanup database connection when app shuts down
@app.teardown_appcontext
def close_db(error):
    """Close database connection when application context ends"""
    if error:
        logger.error(f"Application error: {error}")


# ============================================================================
# NEW ENDPOINTS FOR HYBRID RECOMMENDATION, XAI, AND FEDERATED LEARNING
# ============================================================================

@app.route('/api/ensemble/status', methods=['GET'])
def get_ensemble_status():
    """
    Get Ensemble Recommender Status
    
    Returns current model weights and vote matrix from last recommendation.
    """
    try:
        ensemble = get_ensemble_recommender()
        
        return jsonify({
            'success': True,
            'weights': ensemble.get_model_weights(),
            'models': ['semantic', 'tfidf', 'knowledge', 'collaborative'],
            'vote_matrix': ensemble.get_vote_matrix_display()
        })
    except Exception as e:
        logger.error(f"Error getting ensemble status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ensemble/weights', methods=['POST'])
def update_ensemble_weights():
    """
    Update Ensemble Model Weights
    
    Allows manual adjustment of model weights.
    """
    try:
        data = request.get_json()
        weights = data.get('weights', {})
        
        if not weights:
            return jsonify({'success': False, 'error': 'Weights required'}), 400
        
        ensemble = get_ensemble_recommender()
        ensemble.set_model_weights(weights)
        
        logger.info(f"Ensemble weights updated: {weights}")
        
        return jsonify({
            'success': True,
            'message': 'Weights updated successfully',
            'new_weights': ensemble.get_model_weights()
        })
    except Exception as e:
        logger.error(f"Error updating weights: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ensemble/feedback', methods=['POST'])
def submit_prescription_feedback():
    """
    Submit Prescription Feedback for Weight Learning
    
    When a doctor selects a medicine, this updates the model weights
    based on which models correctly predicted the selection.
    """
    try:
        data = request.get_json()
        selected_medicine = data.get('medicine_name')
        
        if not selected_medicine:
            return jsonify({'success': False, 'error': 'Medicine name required'}), 400
        
        ensemble = get_ensemble_recommender()
        ensemble.update_weights_from_feedback(selected_medicine)
        
        logger.info(f"Weights updated from feedback: {selected_medicine}")
        
        return jsonify({
            'success': True,
            'message': 'Weights updated based on feedback',
            'new_weights': ensemble.get_model_weights()
        })
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/fl/status', methods=['GET'])
def get_fl_status():
    """
    Get Federated Learning Status (Real Implementation Only)
    
    Returns metrics from the most recent FL run.
    Only real FL mode is supported.
    """
    try:
        # Real FL mode only
        server_manager = get_fl_server_manager()
        client_manager = get_fl_client_manager()
        
        server_status = server_manager.get_status()
        client_summary = client_manager.get_summary()
        
        return jsonify({
            'success': True,
            'mode': 'real',
            'server': server_status,
            'clients': client_summary,
            'client_details': client_manager.get_client_details()
        })
    except Exception as e:
        logger.error(f"Error getting FL status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/fl_dashboard')
def fl_dashboard():
    """
    Federated Learning Dashboard
    
    Visual interface for monitoring federated learning training.
    """
    return render_template('fl_dashboard.html')


@app.route('/api/fl/simulate', methods=['POST'])
def run_fl_simulation():
    """
    Run Federated Learning (Real Implementation Only)
    
    Runs FL training with configurable parameters.
    Only real FL mode is supported - no simulation.
    
    Request body:
    {
        "num_rounds": int,
        "num_clients": int,
        "local_epochs": int,
        "learning_rate": float,
        ... (other config parameters)
    }
    """
    try:
        data = request.get_json() or {}
        
        # Real FL mode for Recommender
        logger.info("Starting real federated learning for Hybrid Recommender")
        
        from modules.federated.fl_config import FLConfig
        from modules.federated.recommender_flower_server import RecommenderFLServerManager
        from modules.federated.recommender_data_loader import RecommenderFLDataLoader
        from modules.federated.recommender_flower_client import create_recommender_client_fn
        
        # Get database connection
        db = get_db()
        
        # Create config
        config = FLConfig(
            num_rounds=data.get('num_rounds', 5),
            num_simulated_clients=data.get('num_clients', 3),
            local_epochs=data.get('local_epochs', 1),
            learning_rate=data.get('learning_rate', 0.1),  # Higher LR for weight updates
            data_dir=data.get('data_dir', 'data/sessions'),
            data_split=data.get('data_split', 'iid'),
            use_simulation=False,
            deployment_mode=data.get('deployment_mode', 'local'),
            db_path=data.get('db_path', 'pharmacy.db')
        )
        
        # Load and split prescription data
        data_loader = RecommenderFLDataLoader(
            db_connection=db,
            data_dir=config.data_dir
        )
        
        client_data_splits = data_loader.split_data(
            num_clients=config.num_simulated_clients,
            split_type=config.data_split,
            seed=config.data_seed
        )
        
        # Create client function
        client_fn = create_recommender_client_fn(
            client_data_splits=client_data_splits,
            config={
                "db_connection": db,
                "learning_rate": config.learning_rate,
                "local_epochs": config.local_epochs,
                "data_dir": config.data_dir,
                "checkpoint_dir": config.checkpoint_dir
            }
        )
        
        # Create server manager
        server_manager = RecommenderFLServerManager(config=config, client_fn=client_fn)
        
        # Run federated learning
        results = server_manager.run_federated_learning(
            server_address=config.server_address
        )
        
        logger.info("Recommender FL complete")
        
        return jsonify({
            'success': True,
            'mode': 'real',
            'message': 'Federated learning complete',
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Error running FL: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/fl/progress', methods=['GET'])
def get_fl_progress():
    """
    Get Real-time Training Progress
    
    Returns current training progress and status.
    """
    try:
        server_manager = get_fl_server_manager()
        status = server_manager.get_status()
        
        return jsonify({
            'success': True,
            'progress': {
                'current_round': status['current_round'],
                'total_rounds': status['total_rounds'],
                'progress_percent': status.get('progress_percent', 0),
                'is_running': status['is_running'],
                'latest_metrics': status['round_metrics'][-1] if status['round_metrics'] else None
            }
        })
    except Exception as e:
        logger.error(f"Error getting FL progress: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/fl/start', methods=['POST'])
def start_fl_server():
    """
    Start Flower Server
    
    Starts the Flower server for distributed federated learning.
    Clients can then connect to participate.
    """
    try:
        data = request.get_json() or {}
        
        from modules.federated.fl_config import FLConfig
        from modules.federated.recommender_flower_server import RecommenderFLServerManager
        
        config = FLConfig(
            num_rounds=data.get('num_rounds', 10),
            server_address=data.get('server_address', '0.0.0.0:8080'),
            use_simulation=False
        )
        
        server_manager = get_fl_server_manager()
        server_manager.start_server(server_address=config.server_address)
        
        return jsonify({
            'success': True,
            'message': f'Flower server started on {config.server_address}',
            'server_address': config.server_address
        })
    except Exception as e:
        logger.error(f"Error starting FL server: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/fl/register-client', methods=['POST'])
def register_fl_client():
    """
    Register a Federated Learning Client
    
    Registers a client for distributed federated learning.
    """
    try:
        data = request.get_json() or {}
        
        client_id = data.get('client_id')
        if not client_id:
            return jsonify({'success': False, 'error': 'client_id required'}), 400
        
        client_manager = get_fl_client_manager()
        
        success = client_manager.register_client(
            client_id=client_id,
            data_size=data.get('data_size', 0),
            capabilities=data.get('capabilities', {}),
            metadata=data.get('metadata', {})
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Client {client_id} registered',
                'client_id': client_id
            })
        else:
            return jsonify({'success': False, 'error': 'Registration failed'}), 500
    
    except Exception as e:
        logger.error(f"Error registering client: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/fl/heartbeat', methods=['POST'])
def client_heartbeat():
    """
    Client Heartbeat
    
    Clients send heartbeat to indicate they're alive.
    """
    try:
        data = request.get_json() or {}
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({'success': False, 'error': 'client_id required'}), 400
        
        client_manager = get_fl_client_manager()
        success = client_manager.record_heartbeat(client_id)
        
        return jsonify({
            'success': success,
            'message': 'Heartbeat recorded' if success else 'Client not found'
        })
    
    except Exception as e:
        logger.error(f"Error recording heartbeat: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/fl/metrics', methods=['GET'])
def get_fl_metrics():
    """
    Get Federated Learning Metrics History
    
    Returns complete metrics history for visualization.
    """
    try:
        server_manager = get_fl_server_manager()
        metrics_history = server_manager.get_metrics_history()
        
        return jsonify({
            'success': True,
            'metrics': metrics_history
        })
    except Exception as e:
        logger.error(f"Error getting FL metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/fl/learning-stats', methods=['GET'])
def get_learning_stats():
    """
    Get Incremental Learning Statistics
    
    Returns cumulative learning statistics, recent events, and weight evolution.
    """
    try:
        history = get_learning_history()
        learner = get_incremental_learner()
        
        stats = history.get_stats()
        recent_events = history.get_recent_events(limit=10)
        today_events = history.get_today_events()
        weight_evolution = history.get_weight_evolution()
        learning_rate = history.get_learning_rate()
        current_weights = learner.get_current_weights()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_learnings': stats.get('total_learnings', 0),
                'today_count': stats.get('today_count', 0),
                'last_learning': stats.get('last_learning'),
                'learning_rate_per_hour': round(learning_rate, 2),
                'current_weights': current_weights
            },
            'recent_events': recent_events,
            'today_events': today_events,
            'weight_evolution': weight_evolution[-20:] if len(weight_evolution) > 20 else weight_evolution,  # Last 20 points
            'medicine_patterns': stats.get('medicine_patterns', {})
        })
    except Exception as e:
        logger.error(f"Error getting learning stats: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/fl/learning-history', methods=['GET'])
def get_learning_history_endpoint():
    """
    Get Learning History
    
    Returns full learning history with optional filters.
    """
    try:
        history = get_learning_history()
        
        # Get query parameters
        limit = request.args.get('limit', type=int, default=50)
        offset = request.args.get('offset', type=int, default=0)
        
        all_events = history.history
        total = len(all_events)
        
        # Apply pagination
        paginated_events = all_events[offset:offset+limit]
        
        return jsonify({
            'success': True,
            'events': paginated_events,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        logger.error(f"Error getting learning history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/recommend/hybrid/<patient_id>', methods=['POST'])
def hybrid_recommend(patient_id):
    """
    Hybrid Recommendation with Ensemble Voting
    
    Uses all 4 recommendation models and returns results with explanations.
    """
    try:
        data = request.get_json()
        symptoms = data.get('symptoms', '')
        top_n = data.get('top_n', 5)
        
        if not symptoms:
            return jsonify({'success': False, 'error': 'Symptoms required'}), 400
        
        logger.info(f"Generating hybrid recommendations for patient: {patient_id}")
        
        # Get medicines from database
        db = get_db()
        all_medicines = db.get_all_medicines()
        
        # Get ensemble recommendations
        ensemble = get_ensemble_recommender()
        ensemble.set_database(db)
        recommendations = ensemble.get_recommendations(symptoms, all_medicines, top_n)
        
        # Add explanations
        xai = get_xai_engine()
        explained_recs = xai.explain_batch(symptoms, recommendations)
        
        logger.info(f"Generated {len(explained_recs)} hybrid recommendations")
        
        return jsonify({
            'success': True,
            'recommendations': explained_recs,
            'weights': ensemble.get_model_weights(),
            'vote_matrix': ensemble.get_vote_matrix_display()
        })
    except Exception as e:
        logger.error(f"Error in hybrid recommendation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    import sys
    
    # Check if --no-reload flag is passed
    use_reloader = '--no-reload' not in sys.argv
    
    if not use_reloader:
        print("⚠️  Auto-reload disabled for AI processing")
        sys.argv.remove('--no-reload')
    
    # Run the Flask development server
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=use_reloader)
