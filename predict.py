# predict.py
import os
import joblib
import json
import numpy as np
from datetime import datetime, timezone

from main import app  # Use the existing app instance
from models import db, PatientData, WellnessLog, Prediction, User

MODEL_DIR = "models"
MODEL_FILE = os.path.join(MODEL_DIR, "ivf_success_model.pkl")
META_FILE = os.path.join(MODEL_DIR, "ivf_model_metadata.json")

def load_model_and_meta():
    if not os.path.exists(MODEL_FILE) or not os.path.exists(META_FILE):
        raise FileNotFoundError("Model or metadata files not found. Run train_model.py first.")
    model = joblib.load(MODEL_FILE)
    meta = json.load(open(META_FILE, "r"))
    return model, meta

def build_feature_vector(user_id, meta):
    """
    Read PatientData and latest WellnessLog for user_id and return np.array([features])
    Fallbacks are used for missing values.
    """
    with app.app_context():
        pat = PatientData.query.filter_by(user_id=user_id).first()
        if not pat:
            raise ValueError(f"No PatientData found for user_id={user_id}. Please complete your medical profile.")
        # latest wellness log
        wl = WellnessLog.query.filter_by(user_id=user_id).order_by(WellnessLog.date.desc()).first()

        # Map model features to DB columns with sensible fallbacks
        # Note: BMI calculation fallback if not directly stored or if height/weight are missing
        bmi_val = getattr(pat, "bmi", None)
        if bmi_val is None and getattr(pat, "height", None) and getattr(pat, "weight", None):
            height_m = pat.height / 100
            if height_m > 0:
                bmi_val = pat.weight / (height_m ** 2)
        
        mapping = {
            "age": getattr(pat, "age", None) or 30,
            "bmi": bmi_val or 22.5, # Default BMI
            "amh": getattr(pat, "amh_level", None) or 2.5,
            "fsh": getattr(pat, "fsh_level", None) or 6.0,
            "previous_ivf": getattr(pat, "previous_ivf_cycles", 0) or 0,
            "stress": wl.stress_level if wl and wl.stress_level is not None else 3,
            "sleep_hours": wl.sleep_hours if wl and wl.sleep_hours is not None else 7.0,
            "exercise_min": wl.exercise_minutes if wl and wl.exercise_minutes is not None else 30
        }

        feat_order = meta["feature_order"]
        # Ensure all values are float for the model
        fv = np.array([[float(mapping.get(f, 0)) for f in feat_order]]) # Use .get with default 0 for safety
        return fv, mapping

def predict_and_store(user_id):
    model, meta = load_model_and_meta()
    fv, mapping = build_feature_vector(user_id, meta)
    proba = model.predict_proba(fv)[0] if hasattr(model, "predict_proba") else None
    pred = int(model.predict(fv)[0])

    # store in Prediction table
    with app.app_context():
        p = Prediction(
            user_id=user_id,
            prediction_date=datetime.now(timezone.utc), # Use timezone-aware datetime
            success_probability=float(proba[1]) if proba is not None else float(pred),
            protocol_recommendation=None, # This model doesn't predict protocol, so leave as None or add placeholder
            llm_analysis=json.dumps({"model_features": mapping}), # Store features used for transparency
            model_metadata=json.dumps(meta)
        )
        db.session.add(p)
        db.session.commit()
        return {"prediction": pred, "probability": float(proba[1]) if proba is not None else None, "prediction_id": p.id}

def predict_from_features(features_dict, meta):
    """
    Predict IVF success from a dictionary of features.
    features_dict should have keys matching the model's feature_order, with defaults if missing.
    Returns dict with prediction, probability, etc.
    """
    model, _ = load_model_and_meta()  # meta is already loaded, but we need model

    # Map features_dict to the expected keys, with defaults
    mapping = {
        "age": features_dict.get("age", 30),
        "bmi": features_dict.get("bmi", 22.5),
        "amh": features_dict.get("amh", 2.5),
        "fsh": features_dict.get("fsh", 6.0),
        "previous_ivf": features_dict.get("previous_ivf", 0),
        "stress": features_dict.get("stress", 3),
        "sleep_hours": features_dict.get("sleep_hours", 7.0),
        "exercise_min": features_dict.get("exercise_min", 30)
    }

    feat_order = meta["feature_order"]
    fv = np.array([[float(mapping.get(f, 0)) for f in feat_order]])
    proba = model.predict_proba(fv)[0] if hasattr(model, "predict_proba") else None
    pred = int(model.predict(fv)[0])

    probability = float(proba[1]) if proba is not None else float(pred)
    prediction_text = "Success Likely" if probability >= 0.5 else "Success Unlikely"

    return {
        "prediction": pred,
        "success_probability": round(probability * 100, 1),  # as percentage
        "prediction_text": prediction_text,
        "features_used": mapping
    }

if __name__ == "__main__":
    # quick manual test - change user_id as needed
    import sys
    if len(sys.argv) < 2:
        print("Usage: python predict.py <user_id>")
        sys.exit(1)
    uid = int(sys.argv[1])
    out = predict_and_store(uid)
    print("Stored prediction:", out)
