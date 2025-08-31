import os
import json
from datetime import datetime, date
from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from app import app, db
from models import User, PatientData, IVFCycle, WellnessLog, MedicationReminder, ChatMessage, MedicalDocument
from openai_service import get_chatbot_response, generate_medical_image, get_nutrition_plan, get_yoga_routine
from prediction_service import calculate_ivf_success_prediction, calculate_embryo_quality_score, generate_personalized_protocol

# Utility functions
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Authentication routes
@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.user_type == 'doctor':
            return redirect(url_for('doctor_dashboard'))
        else:
            return redirect(url_for('patient_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            flash(f'Welcome back, {user.first_name}!', 'success')
            
            if user.user_type == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(url_for('patient_dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
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
            flash('Registration failed. Email or username may already exist.', 'error')
    
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
    
    # Get latest cycle
    latest_cycle = IVFCycle.query.filter_by(user_id=user.id).order_by(IVFCycle.created_at.desc()).first()
    
    # Get recent wellness logs
    recent_wellness = WellnessLog.query.filter_by(user_id=user.id).order_by(WellnessLog.date.desc()).limit(7).all()
    
    # Get active medications
    active_medications = MedicationReminder.query.filter_by(user_id=user.id, is_active=True).all()
    
    return render_template('patient_dashboard.html', 
                         user=user, 
                         latest_cycle=latest_cycle,
                         recent_wellness=recent_wellness,
                         active_medications=active_medications)

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
    
    return render_template('doctor_dashboard.html', 
                         user=user, 
                         patients=patients,
                         recent_cycles=recent_cycles)

# IVF Prediction and Analysis
@app.route('/prediction')
@login_required
def prediction():
    user = User.query.get(session['user_id'])
    patient_data = PatientData.query.filter_by(user_id=user.id).first()
    
    if not patient_data:
        flash('Please complete your medical profile first.', 'error')
        return redirect(url_for('update_profile'))
    
    # Calculate predictions
    success_prediction = calculate_ivf_success_prediction(patient_data)
    embryo_quality_score = calculate_embryo_quality_score(patient_data)
    protocol_recommendations = generate_personalized_protocol(patient_data)
    
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
        wellness_log = WellnessLog(
            user_id=user.id,
            mood_rating=int(request.form.get('mood_rating', 0)),
            mood_notes=request.form.get('mood_notes'),
            stress_level=int(request.form.get('stress_level', 0)),
            stress_factors=request.form.get('stress_factors'),
            sleep_hours=float(request.form.get('sleep_hours', 0)),
            sleep_quality=int(request.form.get('sleep_quality', 0)),
            sleep_notes=request.form.get('sleep_notes'),
            symptoms=request.form.get('symptoms'),
            energy_level=int(request.form.get('energy_level', 0)),
            exercise_minutes=int(request.form.get('exercise_minutes', 0)),
            meditation_minutes=int(request.form.get('meditation_minutes', 0)),
            yoga_practiced=bool(request.form.get('yoga_practiced')),
            water_intake=int(request.form.get('water_intake', 0)),
            nutrition_score=int(request.form.get('nutrition_score', 0)),
            supplements_taken=request.form.get('supplements_taken')
        )
        
        db.session.add(wellness_log)
        db.session.commit()
        flash('Wellness log saved successfully!', 'success')
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
    
    # Get AI-generated nutrition plan
    nutrition_plan = get_nutrition_plan(patient_data)
    yoga_routine = get_yoga_routine(patient_data)
    
    return render_template('nutrition.html', 
                         user=user, 
                         nutrition_plan=nutrition_plan,
                         yoga_routine=yoga_routine)

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
        
        # Update patient data
        if request.form.get('age'):
            patient_data.age = int(request.form['age'])
        if request.form.get('height'):
            patient_data.height = float(request.form['height'])
        if request.form.get('weight'):
            patient_data.weight = float(request.form['weight'])
            # Calculate BMI
            if patient_data.height:
                patient_data.bmi = patient_data.weight / ((patient_data.height / 100) ** 2)
        
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
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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

# Chat API
@app.route('/api/chat', methods=['POST'])
@login_required
def chat_api():
    try:
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        user = User.query.get(session['user_id'])
        patient_data = None
        if user.user_type == 'patient':
            patient_data = PatientData.query.filter_by(user_id=user.id).first()
        
        # Get AI response
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
        
        image_url = generate_medical_image(prompt)
        return jsonify({'image_url': image_url})
        
    except Exception as e:
        app.logger.error(f"Image generation error: {str(e)}")
        return jsonify({'error': 'Failed to generate image'}), 500
