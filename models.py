# models.py - FINAL CORRECTED VERSION

from datetime import datetime, date, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from database import db


# --- Core Models ---

class User(db.Model):
    """
    User model for authentication and role management (Patient/Doctor/Admin).
    """
    __tablename__ = 'user' # <-- CRITICAL FIX: Explicit table name added
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    date_of_birth = db.Column(db.Date)
    phone = db.Column(db.String(20))
    
    # 'patient', 'doctor', or 'admin'
    user_type = db.Column(db.String(10), default='patient', nullable=False)
    
    # Link to a clinic if the user is a doctor
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=True) # References 'clinic' table
    
    # Use timezone-aware object for modern stability (FIX)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships (one-to-many/one-to-one)
    patient_data = db.relationship('PatientData', backref='owner', uselist=False, cascade="all, delete-orphan")
    ivf_cycles = db.relationship('IVFCycle', backref='patient', lazy='dynamic', cascade="all, delete-orphan")
    medication_reminders = db.relationship('MedicationReminder', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    wellness_logs = db.relationship('WellnessLog', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    predictions = db.relationship('Prediction', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    chat_messages = db.relationship('ChatMessage', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    medical_documents = db.relationship('MedicalDocument', backref='user', lazy='dynamic', cascade="all, delete-orphan") 
    
    def set_password(self, password):
        """Hashes the password for secure storage."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks the provided password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self):
        """Generates a secure, timed token for password reset."""
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        """
        Verifies the password reset token.
        Returns the User object if the token is valid, otherwise None.
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f'<User {self.username} ({self.user_type})>'


class PatientData(db.Model):
    """
    Stores comprehensive medical and lifestyle data for AI analysis.
    One-to-one relationship with User (only users with user_type='patient').
    """
    __tablename__ = 'patient_data' # <-- CRITICAL FIX: Explicit table name added
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False) # References 'user' table

    # Physical/Hormonal Data
    age = db.Column(db.Integer)
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    bmi = db.Column(db.Float)
    amh_level = db.Column(db.Float) # Anti-Mullerian Hormone (ng/mL)
    fsh_level = db.Column(db.Float) # Follicle-Stimulating Hormone (mIU/mL)
    
    # History
    previous_pregnancies = db.Column(db.Integer, default=0)
    previous_ivf_cycles = db.Column(db.Integer, default=0)
    diagnosis = db.Column(db.Text) # Primary cause of infertility
    medical_history = db.Column(db.Text) # PCOS, Endometriosis, Thyroid issues, etc.
    allergies = db.Column(db.Text)
    
    # Partner & Lifestyle
    partner_age = db.Column(db.Integer)
    partner_diagnosis = db.Column(db.String(255))
    lifestyle_factors = db.Column(db.Text) # Smoking, alcohol, diet, exercise habits

    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def calculate_bmi(self):
        """Calculates BMI (Body Mass Index) from height and weight."""
        if self.height and self.weight:
            # BMI = weight (kg) / (height (m))^2
            height_m = self.height / 100
            if height_m > 0:
                self.bmi = self.weight / (height_m ** 2)
            else:
                 self.bmi = None
        else:
            self.bmi = None

    # Override __init__ to automatically calculate BMI when data is set
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculate_bmi()

    def __repr__(self):
        return f'<PatientData for User {self.user_id}>'


class Clinic(db.Model):
    """Stores information about IVF clinics."""
    __tablename__ = 'clinic' # <-- CRITICAL FIX: Explicit table name added
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    contact_number = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    website = db.Column(db.String(255))
    description = db.Column(db.Text)
    latitude = db.Column(db.Float)  # Latitude for map markers
    longitude = db.Column(db.Float)  # Longitude for map markers

    # Relationship to doctors working at this clinic
    doctors = db.relationship('User', backref='clinic', lazy='dynamic') # References 'user' table via clinic_id foreign key

    def __repr__(self):
        return f'<Clinic {self.name}>'


class IVFCycle(db.Model):
    """
    Tracks a specific IVF treatment cycle from stimulation to outcome.
    """
    __tablename__ = 'ivf_cycle' # <-- CRITICAL FIX: Explicit table name added
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # References 'user' table

    protocol = db.Column(db.String(100)) # e.g., Antagonist, Agonist
    start_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='stimulation') # stimulation, retrieval, transfer, wait, complete
    
    # Key Milestones
    egg_retrieval_date = db.Column(db.Date)
    num_eggs_retrieved = db.Column(db.Integer)
    fertilization_rate = db.Column(db.Float) # Percentage (0.0 to 1.0)
    num_embryos_day5 = db.Column(db.Integer)
    
    transfer_date = db.Column(db.Date)
    num_embryos_transferred = db.Column(db.Integer)
    outcome = db.Column(db.String(50)) # BFN, BFP, Miscarriage, Live Birth

    # Renaming original notes to be patient-specific
    patient_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to doctor's notes
    doctor_notes = db.relationship('CycleNote', backref='cycle', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<IVFCycle {self.id} for Patient {self.patient_id} ({self.protocol})>'


class CycleNote(db.Model):
    """Stores notes made by doctors on a specific IVF cycle."""
    __tablename__ = 'cycle_note' # <-- CRITICAL FIX: Explicit table name added
    id = db.Column(db.Integer, primary_key=True)
    cycle_id = db.Column(db.Integer, db.ForeignKey('ivf_cycle.id'), nullable=False) # References 'ivf_cycle' table
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # References 'user' table
    note_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to the doctor who wrote the note
    doctor = db.relationship('User', backref=db.backref('authored_notes', lazy='dynamic'))

    def __repr__(self):
        return f'<CycleNote {self.id} for Cycle {self.cycle_id} by Doctor {self.doctor_id}>'


class WellnessLog(db.Model):
    """
    Daily log for patient-reported symptoms, mood, and lifestyle factors.
    """
    __tablename__ = 'wellness_log' # <-- CRITICAL FIX: Explicit table name added
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # FIX: Using date.today for non-deprecated date tracking # <-- FINAL FIX 
    date = db.Column(db.Date, default=date.today, nullable=False)
    # Ratings (1=Very Poor, 5=Excellent)
    mood_rating = db.Column(db.Integer) # 1-5
    stress_level = db.Column(db.Integer) # 1-5
    sleep_quality = db.Column(db.Integer) # 1-5
    energy_level = db.Column(db.Integer) # 1-5
    nutrition_score = db.Column(db.Integer) # 1-5
    
    # Metrics
    sleep_hours = db.Column(db.Float)
    exercise_minutes = db.Column(db.Integer, default=0)
    meditation_minutes = db.Column(db.Integer, default=0)
    water_intake = db.Column(db.Integer, default=0) # in ml or glasses
    
    # Booleans
    yoga_practiced = db.Column(db.Boolean, default=False)
    
    # Qualitative Data
    symptoms = db.Column(db.Text) # Free text about physical symptoms
    mood_notes = db.Column(db.Text)
    stress_factors = db.Column(db.Text)
    sleep_notes = db.Column(db.Text)
    supplements_taken = db.Column(db.Text)

    # Meal Descriptions
    meal_breakfast = db.Column(db.Text)
    meal_lunch = db.Column(db.Text)
    meal_dinner = db.Column(db.Text)
    meal_snacks = db.Column(db.Text)

    # AI-detected emotion from mood_notes
    detected_emotion = db.Column(db.String(50))

    # Ensures a user can only log one entry per day
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='_user_date_uc'),)

    def __repr__(self):
        return f'<WellnessLog {self.date} for User {self.user_id}>'


class MedicationReminder(db.Model):
    """
    Stores medication schedules for reminders and tracking.
    """
    __tablename__ = 'medication_reminder' # <-- CRITICAL FIX: Explicit table name added
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    medication_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50))
    frequency = db.Column(db.String(50)) # e.g., Daily, Twice Daily
    time_of_day = db.Column(db.Time) # Time of the day for the reminder
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date) # Null if ongoing

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<MedicationReminder {self.medication_name} for User {self.user_id}>'


class ChatMessage(db.Model):
    """
    Stores chat messages between users and the AI chatbot.
    """
    __tablename__ = 'chat_message' # <-- CRITICAL FIX: Explicit table name added
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ChatMessage {self.id} for User {self.user_id}>'


class MedicalDocument(db.Model):
    """
    Stores metadata for uploaded medical documents.
    """
    __tablename__ = 'medical_document' # <-- CRITICAL FIX: Explicit table name added
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    filename = db.Column(db.String(255), nullable=False) # Stored filename
    original_filename = db.Column(db.String(255), nullable=False) # Original filename
    file_type = db.Column(db.String(100)) # MIME type
    file_size = db.Column(db.Integer) # Size in bytes
    description = db.Column(db.Text)
    extracted_text = db.Column(db.Text) # Extracted text from OCR/PDF processing
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<MedicalDocument {self.filename} for User {self.user_id}>'


class Prediction(db.Model):
    """
    Stores the results of the AI model's success prediction and recommendation.
    """
    __tablename__ = 'prediction' # <-- CRITICAL FIX: Explicit table name added
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    prediction_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # AI Results
    success_probability = db.Column(db.Float) # Score (0.0 to 1.0)

    # Personalized Protocol Recommendation
    protocol_recommendation = db.Column(db.String(100))

    # Detailed text output from the LLM based on grounded search/analysis
    llm_analysis = db.Column(db.Text)

    # Metadata for the prediction (e.g., features used, model version)
    model_metadata = db.Column(db.Text)

    def __repr__(self):
        return f'<Prediction {self.id} ({self.success_probability:.2f}) for User {self.user_id}>'


class MedicalActivity(db.Model):
    """
    Stores medical activities performed on patients (injections, scans, blood work, etc.).
    """
    __tablename__ = 'medical_activity'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # injection, scan, bloodwork, consultation, embryo_transfer, egg_retrieval
    activity_name = db.Column(db.String(255), nullable=False)
    dosage = db.Column(db.String(100))  # For medications/injections
    performed_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    results = db.Column(db.Text)  # Test results or observations
    notes = db.Column(db.Text)

    # Relationship to patient
    patient = db.relationship('User', backref='medical_activities')

    def __repr__(self):
        return f'<MedicalActivity {self.activity_type}: {self.activity_name} for Patient {self.patient_id}>'
