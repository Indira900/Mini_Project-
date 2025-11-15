# routes.py

# This file should not be run directly
if __name__ == "__main__":
    print("This file contains Flask routes and should not be run directly. Run 'python main.py' instead.")
    exit(1)

import os
import json
from datetime import datetime, date
from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from functools import wraps
from werkzeug.utils import secure_filename
from main import app
from database import db
from models import User, PatientData, IVFCycle, WellnessLog, MedicationReminder, ChatMessage, MedicalDocument, Prediction, CycleNote, Clinic, MedicalActivity

# --- Import AI and Prediction Services ---
from openai_service import (
    get_chatbot_response,
    generate_medical_image,
    get_nutrition_plan,
    get_yoga_routine,
    get_nutrition_analysis
)
from prediction_service import (
    calculate_ivf_success_prediction,
    calculate_embryo_quality_score,
    generate_personalized_protocol
)


# Utility functions
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'admin':
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapper

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Authentication routes
@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.user_type == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user.user_type == 'doctor':
            return redirect(url_for('doctor_dashboard'))
        else:
            return redirect(url_for('patient_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_type = request.args.get('type', 'general')  # Get type from query param, default to 'general'

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            flash(f'Welcome back, {user.first_name}!', 'success')

            if user.user_type == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.user_type == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(url_for('patient_dashboard'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html', login_type=login_type)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Check if username or email already exists
            if User.query.filter_by(username=request.form['username']).first() or \
               User.query.filter_by(email=request.form['email']).first():
                flash('Username or Email already registered.', 'error')
                return redirect(url_for('register'))

            user = User(
                username=request.form['username'],
                email=request.form['email'],
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                user_type=request.form['user_type'],
                phone=request.form.get('phone'),
                date_of_birth=datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date() if request.form.get('date_of_birth') else None
            )
            user.set_password(request.form['password'])
            
            db.session.add(user)
            db.session.commit()
            
            # Create patient data record if user is a patient
            if user.user_type == 'patient':
                patient_data = PatientData(user_id=user.id)
                db.session.add(patient_data)
                db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            # Log the full error for debugging
            app.logger.error(f"Registration failed: {e}")
            flash('Registration failed due to a server error.', 'error')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

# Dashboard routes
@app.route('/patient_dashboard')
@login_required
def patient_dashboard():
    user = User.query.get(session['user_id'])
    if user.user_type != 'patient':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    patient_data = PatientData.query.filter_by(user_id=user.id).first()
    
    # Get latest cycle for progress tracking
    latest_cycle = IVFCycle.query.filter_by(patient_id=user.id).order_by(IVFCycle.start_date.desc()).first()
    
    # Get the latest prediction for the stat card
    latest_prediction = Prediction.query.filter_by(user_id=user.id).order_by(Prediction.prediction_date.desc()).first()
    
    # Get active medications
    active_medications = MedicationReminder.query.filter_by(user_id=user.id, is_active=True).order_by(MedicationReminder.time_of_day).all()
    
    # Get recent wellness logs for the stat card and list
    recent_wellness = WellnessLog.query.filter_by(user_id=user.id).order_by(WellnessLog.date.desc()).limit(7).all()
    # Check if today's wellness log exists
    today_wellness_log = WellnessLog.query.filter_by(user_id=user.id, date=date.today()).first()
    
    # Get a personalized AI tip (mocked for now)
    ai_tip = get_chatbot_response("Give me one personalized wellness tip for today.", user, patient_data)
    
    return render_template('patient_dashboard.html', 
                          user=user, 
                          patient_data=patient_data,
                          latest_cycle=latest_cycle,
                          latest_prediction=latest_prediction,
                          recent_wellness=recent_wellness,
                          active_medications=active_medications,
                          today_wellness_log_exists=(today_wellness_log is not None),
                          ai_tip=ai_tip)

@app.route('/doctor_dashboard')
@login_required
def doctor_dashboard():
    user = User.query.get(session['user_id'])
    if user.user_type != 'doctor':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))

    # Get all patients
    patients = User.query.filter_by(user_type='patient').all()

    # Get recent cycles
    recent_cycles = IVFCycle.query.order_by(IVFCycle.created_at.desc()).limit(10).all()

    # Get recent medical activities
    recent_activities = MedicalActivity.query.join(User, MedicalActivity.patient_id == User.id).order_by(MedicalActivity.performed_date.desc()).limit(10).all()

    return render_template('doctor_dashboard.html',
                          user=user,
                          patients=patients,
                          recent_cycles=recent_cycles,
                          recent_activities=recent_activities)

# Doctor's personal notes page
@app.route('/my_notes')
@login_required
def my_notes():
    user = User.query.get(session['user_id'])
    if user.user_type != 'doctor':
        flash('Access denied. This page is for doctors only.', 'error')
        return redirect(url_for('patient_dashboard'))

    # Query for all notes written by the current doctor, ordered by most recent
    # Joined with IVFCycle and User to eager load patient info for efficiency
    notes = CycleNote.query.filter_by(doctor_id=user.id).join(IVFCycle).join(User, IVFCycle.patient_id == User.id).order_by(CycleNote.created_at.desc()).all()

    return render_template('my_notes.html', user=user, notes=notes)

# Patient's view of doctor's notes
@app.route('/my_cycle_notes')
@login_required
def my_cycle_notes():
    user = User.query.get(session['user_id'])
    if user.user_type != 'patient':
        flash('Access denied. This page is for patients only.', 'error')
        return redirect(url_for('index'))

    # Query for all notes related to the patient's cycles
    # Eager load related cycle and doctor info for efficiency
    from sqlalchemy.orm import joinedload
    notes = CycleNote.query.join(IVFCycle).filter(IVFCycle.patient_id == user.id).options(
        joinedload(CycleNote.cycle),
        joinedload(CycleNote.doctor)
    ).order_by(CycleNote.created_at.desc()).all()

    return render_template('view_notes.html', user=user, notes=notes)

# Find a Clinic/Doctor page
@app.route('/find_clinic', methods=['GET', 'POST'])
@login_required
def find_clinic():
    user = User.query.get(session['user_id'])
    search_query = request.form.get('search_query', '').strip()
    clinics = []

    if search_query:
        # Search by city, state, zip code, or clinic name
        search_term = f"%{search_query}%"
        clinics = Clinic.query.filter(
            (Clinic.city.ilike(search_term)) |
            (Clinic.state.ilike(search_term)) |
            (Clinic.zip_code.ilike(search_term)) |
            (Clinic.name.ilike(search_term))
        ).all()

    return render_template('find_clinic.html', user=user, clinics=clinics, search_query=search_query)

# --- Admin Routes ---
@app.route('/admin')
@admin_required
def admin_dashboard():
    user = User.query.get(session['user_id'])
    user_count = User.query.count()
    patient_count = User.query.filter_by(user_type='patient').count()
    doctor_count = User.query.filter_by(user_type='doctor').count()
    clinic_count = Clinic.query.count()
    return render_template('admin_dashboard.html', 
                           user=user, user_count=user_count, 
                           clinic_count=clinic_count, patient_count=patient_count,
                           doctor_count=doctor_count)

@app.route('/admin/clinics')
@admin_required
def admin_clinics():
    user = User.query.get(session['user_id'])
    # Eager load the doctors relationship to prevent extra queries in the template
    from sqlalchemy.orm import subqueryload
    clinics = Clinic.query.options(subqueryload(Clinic.doctors)).order_by(Clinic.name).all()
    return render_template('admin_clinics.html', user=user, clinics=clinics)

@app.route('/admin/clinic/add', methods=['GET', 'POST'])
@admin_required
def add_clinic():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        new_clinic = Clinic(
            name=request.form['name'],
            address=request.form.get('address'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            zip_code=request.form.get('zip_code'),
            phone=request.form.get('phone'),
            website=request.form.get('website'),
            latitude=float(request.form.get('latitude')) if request.form.get('latitude') else None,
            longitude=float(request.form.get('longitude')) if request.form.get('longitude') else None
        )
        db.session.add(new_clinic)
        db.session.commit()
        flash('Clinic added successfully!', 'success')
        return redirect(url_for('admin_clinics'))
    return render_template('admin_clinic_form.html', user=user, clinic=None, title="Add New Clinic")

@app.route('/admin/clinic/edit/<int:clinic_id>', methods=['GET', 'POST'])
@admin_required
def edit_clinic(clinic_id):
    user = User.query.get(session['user_id'])
    clinic = Clinic.query.get_or_404(clinic_id)
    if request.method == 'POST':
        clinic.name = request.form['name']
        clinic.address = request.form.get('address')
        clinic.city = request.form.get('city')
        clinic.state = request.form.get('state')
        clinic.zip_code = request.form.get('zip_code')
        clinic.phone = request.form.get('phone')
        clinic.website = request.form.get('website')
        clinic.latitude = float(request.form.get('latitude')) if request.form.get('latitude') else None
        clinic.longitude = float(request.form.get('longitude')) if request.form.get('longitude') else None
        db.session.commit()
        flash('Clinic updated successfully!', 'success')
        return redirect(url_for('admin_clinics'))
    return render_template('admin_clinic_form.html', user=user, clinic=clinic, title="Edit Clinic")

@app.route('/admin/clinic/delete/<int:clinic_id>', methods=['POST'])
@admin_required
def delete_clinic(clinic_id):
    clinic = Clinic.query.get_or_404(clinic_id)
    # Optional: Check if any doctors are assigned to this clinic before deleting
    if clinic.doctors.first():
        flash('Cannot delete clinic. It has doctors assigned to it.', 'error')
        return redirect(url_for('admin_clinics'))
    
    db.session.delete(clinic)
    db.session.commit()
    flash('Clinic deleted successfully.', 'success')
    return redirect(url_for('admin_clinics'))

@app.route('/admin/users')
@admin_required
def admin_users():
    user = User.query.get(session['user_id'])
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', user=user, users=users)

@app.route('/admin/user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user_to_edit = User.query.get_or_404(user_id)
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        new_role = request.form.get('user_type')
        if new_role not in ['patient', 'doctor', 'admin']:
            flash('Invalid user role selected.', 'error')
            return redirect(url_for('admin_users'))
        
        user_to_edit.user_type = new_role
        db.session.commit()
        flash(f'User {user_to_edit.username}\'s role has been updated.', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin_user_form.html', user=user, user_to_edit=user_to_edit, title="Edit User Role")

@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == session['user_id']:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin_users'))
    user_to_delete = User.query.get_or_404(user_id)
    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f'User {user_to_delete.username} has been deleted.', 'success')
    return redirect(url_for('admin_users'))

# IVF Prediction and Analysis
@app.route('/prediction')
@login_required
def prediction():
    user = User.query.get(session['user_id'])
    patient_data = PatientData.query.filter_by(user_id=user.id).first()

    if not patient_data:
        flash('Please complete your medical profile first.', 'error')
        return redirect(url_for('update_profile'))

    # Use ML prediction instead of rule-based
    from predict import predict_and_store
    ml_result = predict_and_store(user.id)
    success_probability = ml_result['probability'] or ml_result['prediction']  # probability is 0-1, prediction is 0 or 1

    # Keep embryo quality and protocol as rule-based for now
    embryo_quality_score = calculate_embryo_quality_score(patient_data)
    protocol_recommendations = generate_personalized_protocol(patient_data)

    # Update the latest prediction in DB (already done in predict_and_store, but ensure protocol etc.)
    latest_pred = Prediction.query.filter_by(user_id=user.id).order_by(Prediction.prediction_date.desc()).first()
    if latest_pred:
        latest_pred.protocol_recommendation = protocol_recommendations.get('protocol_name')
        latest_pred.llm_analysis = json.dumps({
            "embryo_score": embryo_quality_score.get('quality_score'),
            "protocol_optimizations": protocol_recommendations.get('success_optimization')
        })
        db.session.commit()

    # Format success_prediction for template compatibility
    success_prediction = {
        "success_rate": success_probability * 100,
        "confidence": 85,  # Placeholder, since ML doesn't provide confidence
        "factors": [],  # ML doesn't provide factors, leave empty
        "recommendations": protocol_recommendations.get('success_optimization', []),
        "interpretation": "ML-based prediction"
    }

    return render_template('prediction.html',
                          user=user,
                          patient_data=patient_data,
                          success_prediction=success_prediction,
                          embryo_quality_score=embryo_quality_score,
                          protocol_recommendations=protocol_recommendations)

# Wellness tracking
@app.route('/wellness', methods=['GET', 'POST'])
@login_required
def wellness():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        # Safely parse date from form
        date_str = request.form.get('date')
        log_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
        
        # Check if a log for this date already exists
        existing_log = WellnessLog.query.filter_by(user_id=user.id, date=log_date).first()
        
        if existing_log:
            # Update the existing log
            wellness_log = existing_log
            flash_message = 'Wellness log updated successfully!'
        else:
            # Create a new log
            wellness_log = WellnessLog(user_id=user.id, date=log_date)
            db.session.add(wellness_log)
            flash_message = 'Wellness log saved successfully!'

        # Populate or update fields
        wellness_log.mood_rating = int(request.form.get('mood_rating', 0))
        wellness_log.mood_notes = request.form.get('mood_notes')
        wellness_log.stress_level = int(request.form.get('stress_level', 0))
        wellness_log.stress_factors = request.form.get('stress_factors')
        wellness_log.sleep_hours = float(request.form.get('sleep_hours', 0) or 0)
        wellness_log.sleep_quality = int(request.form.get('sleep_quality', 0) or 0)
        wellness_log.sleep_notes = request.form.get('sleep_notes')
        wellness_log.symptoms = request.form.get('symptoms')
        wellness_log.energy_level = int(request.form.get('energy_level', 0))
        wellness_log.exercise_minutes = int(request.form.get('exercise_minutes', 0) or 0)
        wellness_log.meditation_minutes = int(request.form.get('meditation_minutes', 0) or 0)
        wellness_log.yoga_practiced = ('yoga_practiced' in request.form)
        wellness_log.water_intake = int(request.form.get('water_intake', 0) or 0)
        wellness_log.nutrition_score = int(request.form.get('nutrition_score', 0) or 0)
        wellness_log.supplements_taken = request.form.get('supplements_taken')

        # Save meal descriptions
        wellness_log.meal_breakfast = request.form.get('meal_breakfast')
        wellness_log.meal_lunch = request.form.get('meal_lunch')
        wellness_log.meal_dinner = request.form.get('meal_dinner')
        wellness_log.meal_snacks = request.form.get('meal_snacks')
        
        db.session.commit()
        flash(flash_message, 'success')
        return redirect(url_for('wellness'))
    
    # Get recent logs for charts
    recent_logs = WellnessLog.query.filter_by(user_id=user.id).order_by(WellnessLog.date.desc()).limit(30).all()
    
    return render_template('wellness.html', user=user, recent_logs=recent_logs)

# Nutrition guidance
@app.route('/nutrition')
@login_required
def nutrition():
    user = User.query.get(session['user_id'])
    patient_data = PatientData.query.filter_by(user_id=user.id).first()
    
    # Get AI-generated guidance
    nutrition_plan = get_nutrition_plan(patient_data)
    yoga_routine = get_yoga_routine(patient_data)

    # Get today's meal log and generate nutrition summary
    today_log = WellnessLog.query.filter_by(user_id=user.id, date=date.today()).first()
    nutrition_summary = {}

    if today_log and (today_log.meal_breakfast or today_log.meal_lunch or today_log.meal_dinner or today_log.meal_snacks):
        meal_descriptions = {
            "breakfast": today_log.meal_breakfast,
            "lunch": today_log.meal_lunch,
            "dinner": today_log.meal_dinner,
            "snacks": today_log.meal_snacks
        }
        # Remove empty meals before sending to AI
        meal_descriptions = {k: v for k, v in meal_descriptions.items() if v}
        
        if meal_descriptions:
            nutrition_summary = get_nutrition_analysis(meal_descriptions)
    
    return render_template('nutrition.html', 
                          user=user, 
                          nutrition_plan=nutrition_plan,
                          yoga_routine=yoga_routine,
                          today_log=today_log,
                          nutrition_summary=nutrition_summary)

# Profile management
@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    user = User.query.get(session['user_id'])
    patient_data = PatientData.query.filter_by(user_id=user.id).first()
    
    if not patient_data:
        patient_data = PatientData(user_id=user.id)
        db.session.add(patient_data)
    
    if request.method == 'POST':
        # Update user data
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.phone = request.form.get('phone')
        
        if request.form.get('date_of_birth'):
            user.date_of_birth = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date()
        
        # Update patient data with type casting and validation
        if request.form.get('age'):
            patient_data.age = int(request.form['age'])
        
        # Safely handle float conversions
        height_cm = float(request.form.get('height', 0))
        weight_kg = float(request.form.get('weight', 0))
        
        if height_cm > 0:
            patient_data.height = height_cm
        if weight_kg > 0:
            patient_data.weight = weight_kg
            
        # Calculate BMI
        if patient_data.height and patient_data.height > 0 and patient_data.weight:
            patient_data.bmi = patient_data.weight / ((patient_data.height / 100) ** 2)
        else:
            patient_data.bmi = None 
        
        if request.form.get('amh_level'):
            patient_data.amh_level = float(request.form['amh_level'])
        if request.form.get('fsh_level'):
            patient_data.fsh_level = float(request.form['fsh_level'])
            
        patient_data.diagnosis = request.form.get('diagnosis')
        patient_data.medical_history = request.form.get('medical_history')
        patient_data.medications = request.form.get('medications')
        patient_data.allergies = request.form.get('allergies')
        patient_data.lifestyle_factors = request.form.get('lifestyle_factors')
        
        if request.form.get('previous_pregnancies'):
            patient_data.previous_pregnancies = int(request.form['previous_pregnancies'])
        if request.form.get('previous_ivf_cycles'):
            patient_data.previous_ivf_cycles = int(request.form['previous_ivf_cycles'])
        if request.form.get('partner_age'):
            patient_data.partner_age = int(request.form['partner_age'])
            
        patient_data.partner_diagnosis = request.form.get('partner_diagnosis')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient_dashboard'))
    
    return render_template('update_profile.html', user=user, patient_data=patient_data)

# File upload
@app.route('/upload_document', methods=['POST'])
@login_required
def upload_document():
    if 'file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(request.referrer)

    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(request.referrer)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename

        # Ensure the uploads folder exists (done in main.py, but good to ensure)
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)

        document = MedicalDocument(
            user_id=session['user_id'],
            filename=filename,
            original_filename=file.filename,
            file_type=file.content_type,
            file_size=os.path.getsize(file_path),
            description=request.form.get('description')
        )

        db.session.add(document)
        db.session.commit()
        flash('Document uploaded successfully!', 'success')
    else:
        flash('Invalid file type.', 'error')

    return redirect(request.referrer)

# My Documents page
@app.route('/my_documents')
@login_required
def my_documents():
    user = User.query.get(session['user_id'])
    if user.user_type != 'patient':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))

    documents = MedicalDocument.query.filter_by(user_id=user.id).order_by(MedicalDocument.uploaded_at.desc()).all()
    return render_template('my_documents.html', user=user, documents=documents)

# Download document
@app.route('/download_document/<int:doc_id>')
@login_required
def download_document(doc_id):
    document = MedicalDocument.query.get_or_404(doc_id)
    if document.user_id != session['user_id']:
        flash('Access denied.', 'error')
        return redirect(url_for('my_documents'))

    upload_dir = app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_dir, document.filename, as_attachment=True, download_name=document.original_filename)

# Add Doctor's Note to Cycle
@app.route('/add_cycle_note/<int:cycle_id>', methods=['POST'])
@login_required
def add_cycle_note(cycle_id):
    user = User.query.get(session['user_id'])
    if user.user_type != 'doctor':
        flash('Only doctors can add notes.', 'error')
        return redirect(url_for('patient_dashboard'))

    cycle = IVFCycle.query.get_or_404(cycle_id)
    note_content = request.form.get('note_content')

    if not note_content:
        flash('Note content cannot be empty.', 'error')
        return redirect(url_for('doctor_dashboard'))

    new_note = CycleNote(
        cycle_id=cycle.id,
        doctor_id=user.id,
        note_content=note_content
    )
    db.session.add(new_note)
    db.session.commit()
    flash('Note added successfully to the patient\'s cycle.', 'success')
    return redirect(url_for('doctor_dashboard'))

# Create New IVF Cycle
@app.route('/create_cycle', methods=['POST'])
@login_required
def create_cycle():
    user = User.query.get(session['user_id'])
    if user.user_type != 'doctor':
        flash('Only doctors can create cycles.', 'error')
        return redirect(url_for('index'))

    patient_id = request.form.get('patient_id')
    protocol = request.form.get('protocol', 'Antagonist')
    start_date_str = request.form.get('start_date')
    patient_notes = request.form.get('patient_notes')

    if not patient_id or not start_date_str:
        flash('Patient and start date are required.', 'error')
        return redirect(url_for('doctor_dashboard'))

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('doctor_dashboard'))

    # Check if patient exists and is a patient
    patient = User.query.get(patient_id)
    if not patient or patient.user_type != 'patient':
        flash('Invalid patient selected.', 'error')
        return redirect(url_for('doctor_dashboard'))

    new_cycle = IVFCycle(
        patient_id=patient.id,
        protocol=protocol,
        start_date=start_date,
        patient_notes=patient_notes
    )
    db.session.add(new_cycle)
    db.session.commit()
    flash(f'New IVF cycle created for {patient.first_name} {patient.last_name}.', 'success')
    return redirect(url_for('doctor_dashboard'))

# Schedule Appointment
@app.route('/schedule_appointment', methods=['POST'])
@login_required
def schedule_appointment():
    user = User.query.get(session['user_id'])
    if user.user_type != 'doctor':
        flash('Only doctors can schedule appointments.', 'error')
        return redirect(url_for('index'))

    patient_id = request.form.get('patient_id')
    appointment_type = request.form.get('appointment_type')
    appointment_date_str = request.form.get('appointment_date')
    appointment_time_str = request.form.get('appointment_time')
    notes = request.form.get('notes')

    if not all([patient_id, appointment_type, appointment_date_str, appointment_time_str]):
        flash('All fields are required.', 'error')
        return redirect(url_for('doctor_dashboard'))

    try:
        appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
        appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
        performed_date = datetime.combine(appointment_date, appointment_time)
    except ValueError:
        flash('Invalid date or time format.', 'error')
        return redirect(url_for('doctor_dashboard'))

    # Check if patient exists
    patient = User.query.get(patient_id)
    if not patient or patient.user_type != 'patient':
        flash('Invalid patient selected.', 'error')
        return redirect(url_for('doctor_dashboard'))

    new_activity = MedicalActivity(
        patient_id=patient.id,
        activity_type=appointment_type,
        activity_name=f"{appointment_type.title()} Appointment",
        performed_date=performed_date,
        notes=notes
    )
    db.session.add(new_activity)
    db.session.commit()
    flash(f'Appointment scheduled for {patient.first_name} {patient.last_name} on {performed_date.strftime("%B %d, %Y at %I:%M %p")}.', 'success')
    return redirect(url_for('doctor_dashboard'))

# Chat API
@app.route('/api/chat', methods=['POST'])
@login_required
def chat_api():
    try:
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        user = User.query.get(session['user_id']) # type: ignore
        patient_data = None
        if user.user_type == 'patient':
            patient_data = PatientData.query.filter_by(user_id=user.id).first()
        
        # Get AI response (using mock data)
        response = get_chatbot_response(message, user, patient_data)
        
        # Save chat to database
        chat_message = ChatMessage(
            user_id=user.id,
            message=message,
            response=response
        )
        db.session.add(chat_message)
        db.session.commit()
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Chat API error: {str(e)}")
        return jsonify({'error': 'Failed to process chat message'}), 500

# FAQ page
@app.route('/faq')
def faq():
    return render_template('faq.html')

# Chatbot page
@app.route('/chatbot')
@login_required
def chatbot():
    user = User.query.get(session['user_id'])
    return render_template('chatbot.html', user=user)

# API endpoint for wellness data (for charts)
@app.route('/api/wellness_data')
@login_required
def wellness_data():
    user_id = session['user_id']
    logs = WellnessLog.query.filter_by(user_id=user_id).order_by(WellnessLog.date.desc()).limit(30).all()
    
    data = {
        'dates': [log.date.strftime('%Y-%m-%d') for log in reversed(logs)],
        'mood': [log.mood_rating or 0 for log in reversed(logs)],
        'stress': [log.stress_level or 0 for log in reversed(logs)],
        'sleep_hours': [log.sleep_hours or 0 for log in reversed(logs)],
        'sleep_quality': [log.sleep_quality or 0 for log in reversed(logs)],
        'energy': [log.energy_level or 0 for log in reversed(logs)]
    }
    
    return jsonify(data)

# Generate AI image
@app.route('/api/generate_image', methods=['POST'])
@login_required
def generate_image_api():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        # Get AI image URL
        image_url = generate_medical_image(prompt)
        return jsonify({'image_url': image_url})
        
    except Exception as e:
        app.logger.error(f"Image generation error: {str(e)}")
        return jsonify({'error': 'Failed to generate image'}), 500

# IVF Predictor API for direct feature input (no login required)
@app.route('/predict_ivf', methods=['POST'])
def predict_ivf():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Map incoming features to model features (remove LH as it's not in model)
        features = {
            "age": data.get("Age", 30),
            "bmi": data.get("BMI", 22.5),
            "amh": data.get("AMH", 2.5),
            "fsh": data.get("FSH", 6.0),
            "previous_ivf": data.get("Previous_IVF_Attempts", 0),
            "stress": data.get("Stress_Level", 3),
            "sleep_hours": data.get("Sleep_Hours", 7.0),
            "exercise_min": data.get("Exercise_Min_per_Day", 30)
        }

        from predict import load_model_and_meta
        _, meta = load_model_and_meta()
        from predict import predict_from_features
        result = predict_from_features(features, meta)

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"IVF prediction error: {str(e)}")
        return jsonify({'error': 'Failed to predict IVF success'}), 500
