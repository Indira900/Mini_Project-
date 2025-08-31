import os
import json
from openai import OpenAI

# Using GPT-4o which is the latest available model
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "fallback-key")
client = OpenAI(api_key=OPENAI_API_KEY)

def get_chatbot_response(message, user, patient_data=None):
    """Get AI chatbot response for IVF-related questions"""
    try:
        # Build context based on user data
        context = f"You are an AI assistant specialized in IVF (In Vitro Fertilization) support. "
        context += f"You're speaking with {user.first_name}, a {user.user_type}. "
        
        if patient_data:
            context += f"Patient details: Age {patient_data.age}, "
            if patient_data.diagnosis:
                context += f"Diagnosis: {patient_data.diagnosis}, "
            if patient_data.previous_ivf_cycles:
                context += f"Previous IVF cycles: {patient_data.previous_ivf_cycles}, "
        
        context += """
        Provide helpful, accurate, and empathetic responses about:
        - IVF procedures and timelines
        - Medication guidance and side effects
        - Emotional support and encouragement
        - Appointment preparation
        - Lifestyle recommendations
        - Nutritional advice for fertility
        
        Always be supportive and remind users to consult their healthcare provider for medical decisions.
        Keep responses concise but informative.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"I'm sorry, I'm having trouble responding right now. Please try again later. Error: {str(e)}"

def generate_medical_image(prompt):
    """Generate medical illustration using DALL-E"""
    try:
        # Enhance prompt for medical context
        enhanced_prompt = f"Medical illustration: {prompt}, professional medical style, clean, educational, accurate anatomy"
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            n=1,
            size="1024x1024",
            style="natural"
        )
        
        return response.data[0].url
        
    except Exception as e:
        return f"/static/images/placeholder-medical.svg"

def get_nutrition_plan(patient_data):
    """Generate personalized nutrition plan using AI"""
    try:
        context = "Generate a personalized nutrition plan for IVF patients. "
        if patient_data:
            context += f"Patient details: Age {patient_data.age}, BMI {patient_data.bmi}, "
            if patient_data.diagnosis:
                context += f"Diagnosis: {patient_data.diagnosis}"
        
        context += """
        Provide a JSON response with:
        - daily_calories: recommended daily calories
        - key_nutrients: list of important nutrients with benefits
        - meal_suggestions: breakfast, lunch, dinner, snacks
        - foods_to_avoid: list of foods to limit or avoid
        - supplements: recommended supplements
        - hydration: water intake recommendations
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a fertility nutrition specialist. Provide evidence-based nutrition advice for IVF patients."},
                {"role": "user", "content": context}
            ],
            response_format={"type": "json_object"},
            max_tokens=800
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        # Fallback nutrition plan
        return {
            "daily_calories": "1800-2200",
            "key_nutrients": [
                {"name": "Folic Acid", "benefit": "Supports embryo development"},
                {"name": "Iron", "benefit": "Prevents anemia during treatment"},
                {"name": "Calcium", "benefit": "Supports bone health"},
                {"name": "Omega-3", "benefit": "Reduces inflammation"}
            ],
            "meal_suggestions": {
                "breakfast": "Whole grain cereal with berries and yogurt",
                "lunch": "Grilled salmon with quinoa and vegetables",
                "dinner": "Lean chicken with sweet potato and greens",
                "snacks": "Nuts, fruits, and Greek yogurt"
            },
            "foods_to_avoid": [
                "High mercury fish",
                "Excessive caffeine",
                "Processed foods",
                "Trans fats"
            ],
            "supplements": [
                "Prenatal vitamins",
                "Folic acid",
                "Vitamin D",
                "Omega-3"
            ],
            "hydration": "8-10 glasses of water daily"
        }

def get_yoga_routine(patient_data):
    """Generate personalized yoga routine for IVF patients"""
    try:
        context = "Create a gentle yoga routine specifically designed for IVF patients. "
        if patient_data and patient_data.age:
            context += f"Patient age: {patient_data.age}. "
        
        context += """
        Provide a JSON response with:
        - routine_name: name of the routine
        - duration: total duration in minutes
        - poses: list of yoga poses with descriptions and benefits
        - breathing_exercises: breathing techniques
        - meditation: short meditation guidance
        - precautions: important safety notes for IVF patients
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a fertility yoga specialist. Create safe, gentle yoga routines for IVF patients."},
                {"role": "user", "content": context}
            ],
            response_format={"type": "json_object"},
            max_tokens=800
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        # Fallback yoga routine
        return {
            "routine_name": "Gentle IVF Support Routine",
            "duration": "20-30 minutes",
            "poses": [
                {"name": "Child's Pose", "description": "Kneel and sit back on heels, stretch arms forward", "benefit": "Reduces stress and anxiety"},
                {"name": "Cat-Cow Stretch", "description": "On hands and knees, alternate arching and rounding spine", "benefit": "Improves circulation"},
                {"name": "Legs Up the Wall", "description": "Lie on back with legs up against wall", "benefit": "Promotes relaxation and blood flow"},
                {"name": "Butterfly Pose", "description": "Sit with soles of feet together, gently lean forward", "benefit": "Opens hips and pelvis"}
            ],
            "breathing_exercises": [
                "4-7-8 breathing: Inhale for 4, hold for 7, exhale for 8",
                "Box breathing: Equal counts for inhale, hold, exhale, hold"
            ],
            "meditation": "5-minute guided relaxation focusing on positive affirmations and body awareness",
            "precautions": [
                "Avoid deep twists and backbends",
                "No hot yoga during treatment",
                "Listen to your body and rest when needed",
                "Consult your doctor before starting any exercise program"
            ]
        }
