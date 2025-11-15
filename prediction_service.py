import math

def calculate_ivf_success_prediction(patient_data):
    """Calculate IVF success prediction based on multiple factors"""
    if not patient_data:
        return {
            "success_rate": 0,
            "confidence": 0,
            "factors": [],
            "recommendations": []
        }
    
    base_rate = 35.0  # Base success rate percentage
    factors = []
    adjustments = 0
    
    # Age factor (most important)
    if patient_data.age:
        if patient_data.age <= 30:
            age_adjustment = 15
            factors.append({"factor": "Age ≤30", "impact": "+15%", "positive": True})
        elif patient_data.age <= 35:
            age_adjustment = 5
            factors.append({"factor": "Age 31-35", "impact": "+5%", "positive": True})
        elif patient_data.age <= 37:
            age_adjustment = -5
            factors.append({"factor": "Age 36-37", "impact": "-5%", "positive": False})
        elif patient_data.age <= 40:
            age_adjustment = -15
            factors.append({"factor": "Age 38-40", "impact": "-15%", "positive": False})
        else:
            age_adjustment = -25
            factors.append({"factor": "Age >40", "impact": "-25%", "positive": False})
        
        adjustments += age_adjustment
    
    # BMI factor
    if patient_data.bmi:
        if 18.5 <= patient_data.bmi <= 24.9:
            bmi_adjustment = 5
            factors.append({"factor": "Healthy BMI", "impact": "+5%", "positive": True})
        elif patient_data.bmi < 18.5 or patient_data.bmi >= 30:
            bmi_adjustment = -10
            factors.append({"factor": "BMI outside healthy range", "impact": "-10%", "positive": False})
        else:
            bmi_adjustment = -3
            factors.append({"factor": "Borderline BMI", "impact": "-3%", "positive": False})
        
        adjustments += bmi_adjustment
    
    # AMH level factor
    if patient_data.amh_level:
        if patient_data.amh_level >= 2.0:
            amh_adjustment = 8
            factors.append({"factor": "Good AMH level", "impact": "+8%", "positive": True})
        elif patient_data.amh_level >= 1.0:
            amh_adjustment = 2
            factors.append({"factor": "Adequate AMH level", "impact": "+2%", "positive": True})
        else:
            amh_adjustment = -12
            factors.append({"factor": "Low AMH level", "impact": "-12%", "positive": False})
        
        adjustments += amh_adjustment
    
    # Previous IVF cycles factor
    if patient_data.previous_ivf_cycles:
        if patient_data.previous_ivf_cycles == 1:
            cycle_adjustment = -5
            factors.append({"factor": "1 previous cycle", "impact": "-5%", "positive": False})
        elif patient_data.previous_ivf_cycles >= 2:
            cycle_adjustment = -10
            factors.append({"factor": "Multiple previous cycles", "impact": "-10%", "positive": False})
        else:
            cycle_adjustment = 0
        
        adjustments += cycle_adjustment
    else:
        factors.append({"factor": "First IVF attempt", "impact": "+3%", "positive": True})
        adjustments += 3
    
    # Partner age factor
    if patient_data.partner_age:
        if patient_data.partner_age <= 35:
            partner_adjustment = 3
            factors.append({"factor": "Partner age ≤35", "impact": "+3%", "positive": True})
        elif patient_data.partner_age >= 45:
            partner_adjustment = -5
            factors.append({"factor": "Partner age ≥45", "impact": "-5%", "positive": False})
        else:
            partner_adjustment = 0
        
        adjustments += partner_adjustment
    
    # Calculate final success rate
    final_rate = max(5, min(85, base_rate + adjustments))
    
    # Calculate confidence based on available data
    data_points = sum([
        1 if patient_data.age else 0,
        1 if patient_data.bmi else 0,
        1 if patient_data.amh_level else 0,
        1 if patient_data.fsh_level else 0,
        1 if patient_data.partner_age else 0
    ])
    confidence = min(95, 60 + (data_points * 7))
    
    # Generate recommendations
    recommendations = []
    if patient_data.age and patient_data.age > 35:
        recommendations.append("Consider genetic testing of embryos (PGT-A)")
    if patient_data.bmi and (patient_data.bmi < 18.5 or patient_data.bmi >= 25):
        recommendations.append("Optimize weight through nutrition and exercise")
    if patient_data.amh_level and patient_data.amh_level < 1.0:
        recommendations.append("Discuss aggressive stimulation protocols with your doctor")
    if not patient_data.lifestyle_factors:
        recommendations.append("Optimize lifestyle: quit smoking, limit alcohol, manage stress")
    
    return {
        "success_rate": round(final_rate, 1),
        "confidence": confidence,
        "factors": factors,
        "recommendations": recommendations,
        "interpretation": get_success_rate_interpretation(final_rate)
    }

def calculate_embryo_quality_score(patient_data):
    """AI-powered embryo quality predictor (novel feature)"""
    if not patient_data:
        return {
            "quality_score": 0,
            "grade": "Unknown",
            "development_probability": 0,
            "implantation_potential": 0
        }
    
    base_score = 65.0
    adjustments = 0
    
    # Age-based embryo quality
    if patient_data.age:
        if patient_data.age <= 30:
            adjustments += 20
        elif patient_data.age <= 35:
            adjustments += 10
        elif patient_data.age <= 38:
            adjustments += 0
        elif patient_data.age <= 42:
            adjustments -= 15
        else:
            adjustments -= 30
    
    # AMH impact on egg quality
    if patient_data.amh_level:
        if patient_data.amh_level >= 2.0:
            adjustments += 10
        elif patient_data.amh_level >= 1.0:
            adjustments += 5
        else:
            adjustments -= 10
    
    # Lifestyle factors
    if patient_data.lifestyle_factors:
        lifestyle_lower = patient_data.lifestyle_factors.lower()
        if 'non-smoker' in lifestyle_lower or 'no smoking' in lifestyle_lower:
            adjustments += 5
        if 'exercise' in lifestyle_lower or 'active' in lifestyle_lower:
            adjustments += 3
        if 'smoking' in lifestyle_lower:
            adjustments -= 15
    
    final_score = max(10, min(95, base_score + adjustments))
    
    # Determine grade
    if final_score >= 80:
        grade = "A (Excellent)"
    elif final_score >= 65:
        grade = "B (Good)"
    elif final_score >= 45:
        grade = "C (Fair)"
    else:
        grade = "D (Poor)"
    
    # Calculate related probabilities
    development_probability = min(90, final_score * 0.9)
    implantation_potential = min(85, final_score * 0.8)
    
    return {
        "quality_score": round(final_score, 1),
        "grade": grade,
        "development_probability": round(development_probability, 1),
        "implantation_potential": round(implantation_potential, 1),
        "factors": [
            f"Age factor: {patient_data.age if patient_data.age else 'Not provided'}",
            f"AMH level: {patient_data.amh_level if patient_data.amh_level else 'Not provided'}",
            f"Lifestyle: {patient_data.lifestyle_factors if patient_data.lifestyle_factors else 'Not provided'}"
        ]
    }

def generate_personalized_protocol(patient_data):
    """Personalized treatment protocol AI advisor (novel feature)"""
    if not patient_data:
        return {
            "protocol_name": "Standard Protocol",
            "medication_suggestions": [],
            "timing_recommendations": {},
            "success_optimization": []
        }
    
    age = patient_data.age or 35
    amh = patient_data.amh_level or 1.5
    bmi = patient_data.bmi or 24
    
    # Determine protocol based on patient characteristics
    if age <= 35 and amh >= 2.0:
        protocol = "Standard Long Protocol"
        stimulation_days = "10-12 days"
        expected_response = "Good"
    elif age <= 35 and amh < 1.0:
        protocol = "High-Dose Short Protocol"
        stimulation_days = "8-10 days"
        expected_response = "Moderate"
    elif age > 35 and amh >= 1.5:
        protocol = "Antagonist Protocol"
        stimulation_days = "9-11 days"
        expected_response = "Good to Moderate"
    else:
        protocol = "Mini-IVF or Natural Cycle"
        stimulation_days = "5-8 days"
        expected_response = "Low to Moderate"
    
    # Medication suggestions
    medications = []
    if amh < 1.0:
        medications.append("Higher dose FSH (300-450 IU)")
        medications.append("Consider adding LH supplementation")
    else:
        medications.append("Standard dose FSH (150-225 IU)")
    
    if age > 38:
        medications.append("Consider growth hormone supplementation")
    
    if bmi >= 30:
        medications.append("Adjusted dosing for BMI")
    
    # Timing recommendations
    timing = {
        "cycle_start": "Day 2-3 of menstrual cycle",
        "stimulation_duration": stimulation_days,
        "monitoring_frequency": "Every 2-3 days after day 5",
        "trigger_timing": "When 2-3 follicles reach 17-18mm"
    }
    
    # Success optimization tips
    optimization = []
    if patient_data.lifestyle_factors and 'stress' in patient_data.lifestyle_factors.lower():
        optimization.append("Implement stress reduction techniques")
    
    optimization.extend([
        "Maintain optimal weight and nutrition",
        "Consider acupuncture for improved outcomes",
        "Ensure adequate sleep (7-9 hours nightly)",
        "Take prescribed supplements consistently"
    ])
    
    if age > 35:
        optimization.append("Discuss PGT-A testing for embryo selection")
    
    return {
        "protocol_name": protocol,
        "expected_response": expected_response,
        "medication_suggestions": medications,
        "timing_recommendations": timing,
        "success_optimization": optimization,
        "personalization_score": calculate_personalization_score(patient_data)
    }

def calculate_personalization_score(patient_data):
    """Calculate how personalized the protocol is based on available data"""
    data_points = 0
    if patient_data.age: data_points += 1
    if patient_data.amh_level: data_points += 1
    if patient_data.bmi: data_points += 1
    if patient_data.fsh_level: data_points += 1
    if patient_data.previous_ivf_cycles is not None: data_points += 1
    if patient_data.diagnosis: data_points += 1
    if patient_data.lifestyle_factors: data_points += 1
    
    return min(100, (data_points / 7) * 100)

def get_success_rate_interpretation(rate):
    """Provide interpretation of success rate"""
    if rate >= 60:
        return "Excellent prospects - above average success rate"
    elif rate >= 45:
        return "Good prospects - average to above-average success rate"
    elif rate >= 30:
        return "Moderate prospects - consider optimization strategies"
    else:
        return "Challenging case - discuss alternative approaches with your doctor"
