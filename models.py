from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    user_type = db.Column(db.String(20), nullable=False, default='patient')  # patient or doctor
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    patient_data = db.relationship('PatientData', backref='user', lazy=True, uselist=False)
    cycles = db.relationship('IVFCycle', backref='user', lazy=True)
    wellness_logs = db.relationship('WellnessLog', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PatientData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    age = db.Column(db.Integer)
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    bmi = db.Column(db.Float)
    amh_level = db.Column(db.Float)
    fsh_level = db.Column(db.Float)
    diagnosis = db.Column(db.Text)
    previous_pregnancies = db.Column(db.Integer, default=0)
    previous_ivf_cycles = db.Column(db.Integer, default=0)
    medical_history = db.Column(db.Text)
    medications = db.Column(db.Text)
    allergies = db.Column(db.Text)
    lifestyle_factors = db.Column(db.Text)
    partner_age = db.Column(db.Integer)
    partner_diagnosis = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class IVFCycle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cycle_number = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    protocol = db.Column(db.String(100))
    stimulation_start_date = db.Column(db.Date)
    egg_retrieval_date = db.Column(db.Date)
    transfer_date = db.Column(db.Date)
    beta_test_date = db.Column(db.Date)
    
    # Cycle outcomes
    eggs_retrieved = db.Column(db.Integer)
    mature_eggs = db.Column(db.Integer)
    fertilized_eggs = db.Column(db.Integer)
    day3_embryos = db.Column(db.Integer)
    day5_embryos = db.Column(db.Integer)
    transferred_embryos = db.Column(db.Integer)
    frozen_embryos = db.Column(db.Integer)
    
    # Results
    beta_result = db.Column(db.Float)
    pregnancy_outcome = db.Column(db.String(50))
    success_prediction = db.Column(db.Float)
    ai_embryo_quality_score = db.Column(db.Float)
    personalized_protocol_score = db.Column(db.Float)
    
    status = db.Column(db.String(30), default='active')  # active, completed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WellnessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    
    # Mood tracking (1-5 scale)
    mood_rating = db.Column(db.Integer)
    mood_notes = db.Column(db.Text)
    
    # Stress tracking (1-5 scale)
    stress_level = db.Column(db.Integer)
    stress_factors = db.Column(db.Text)
    
    # Sleep tracking
    sleep_hours = db.Column(db.Float)
    sleep_quality = db.Column(db.Integer)  # 1-5 scale
    sleep_notes = db.Column(db.Text)
    
    # Physical symptoms
    symptoms = db.Column(db.Text)
    energy_level = db.Column(db.Integer)  # 1-5 scale
    
    # Activities
    exercise_minutes = db.Column(db.Integer)
    meditation_minutes = db.Column(db.Integer)
    yoga_practiced = db.Column(db.Boolean, default=False)
    
    # Nutrition
    water_intake = db.Column(db.Integer)  # glasses
    nutrition_score = db.Column(db.Integer)  # 1-5 scale
    supplements_taken = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MedicationReminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medication_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50))
    frequency = db.Column(db.String(50))
    time_of_day = db.Column(db.Time)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    instructions = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class MedicalDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    description = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
