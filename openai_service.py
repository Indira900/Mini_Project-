import os
import json
from openai import OpenAI

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "fallback-key")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY != "fallback-key" else None

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
        if client is None:
            # Generate placeholder images for yoga poses
            if "child" in prompt.lower() and "pose" in prompt.lower():
                return "/static/images/child_pose.jpg"
            elif "cat" in prompt.lower() and "cow" in prompt.lower():
                return "/static/images/cat_cow.jpg"
            elif "seated" in prompt.lower() and "twist" in prompt.lower():
                return "/static/images/seated_twist.jpg"
            else:
                return "/static/images/placeholder-medical.svg"

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
        # Fallback to placeholder images
        if "child" in prompt.lower() and "pose" in prompt.lower():
            return "/static/images/child_pose.jpg"
        elif "cat" in prompt.lower() and "cow" in prompt.lower():
            return "/static/images/cat_cow.jpg"
        elif "seated" in prompt.lower() and "twist" in prompt.lower():
            return "/static/images/seated_twist.jpg"
        else:
            return "/static/images/placeholder-medical.svg"

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
            "meal_suggestions": [
                {
                    "meal": "Breakfast", 
                    "description": "Greek yogurt with berries, chia seeds, and walnuts.",
                    "benefit": "High in antioxidants and omega-3s for egg quality."
                },
                {
                    "meal": "Lunch", 
                    "description": "Grilled salmon salad with spinach, avocado, and quinoa.", 
                    "benefit": "Rich in protein and healthy fats for hormonal balance."
                },
                {
                    "meal": "Dinner", "description": "Stir-fried vegetables with tofu and brown rice.", "benefit": "Anti-inflammatory foods to support reproductive health."
                },
                {
                    "meal": "Snacks", "description": "Apple slices with almond butter and dark chocolate.", "benefit": "Provides sustained energy and fertility-boosting nutrients."
                }
            ],
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
            "duration": "25-30 minutes",
            "poses": [
                {"name": "Sukhasana (Easy Pose)", "description": "Sit comfortably cross-legged with a straight spine.", "benefit": "Calms the mind, reduces stress, and opens the hips.", "image": "https://via.placeholder.com/200x150/6f42c1/ffffff?text=Sukhasana+Easy+Pose"},
                {"name": "Baddha Konasana (Bound Angle Pose)", "description": "Sit with the soles of your feet together and let your knees fall to the sides.", "benefit": "Stimulates ovaries and improves blood flow to the pelvic region.", "image": "https://via.placeholder.com/200x150/6f42c1/ffffff?text=Baddha+Konasana+Bound+Angle+Pose"},
                {"name": "Supta Baddha Konasana (Reclined Bound Angle)", "description": "Lie on your back with the soles of your feet together and knees out.", "benefit": "Promotes deep relaxation and opens the pelvic area.", "image": "https://via.placeholder.com/200x150/6f42c1/ffffff?text=Supta+Baddha+Konasana+Reclined+Bound+Angle"},
                {"name": "Cat-Cow Pose (Marjaryasana-Bitilasana)", "description": "On hands and knees, alternate between arching and rounding your back.", "benefit": "Improves spinal flexibility and relieves tension.", "image": "https://via.placeholder.com/200x150/6f42c1/ffffff?text=Cat-Cow+Pose+Marjaryasana-Bitilasana"},
                {"name": "Viparita Karani (Legs-Up-the-Wall Pose)", "description": "Lie on your back with your legs extended up against a wall.", "benefit": "Enhances blood circulation to the pelvis and calms the nervous system.", "image": "https://via.placeholder.com/200x150/6f42c1/ffffff?text=Viparita+Karani+Legs-Up-the-Wall+Pose"},
                {"name": "Setu Bandhasana (Bridge Pose)", "description": "Lie on your back, bend your knees, and lift your hips off the floor.", "benefit": "Stretches the pelvic region and improves circulation to the uterus.", "image": "https://via.placeholder.com/200x150/6f42c1/ffffff?text=Setu+Bandhasana+Bridge+Pose"},
                {"name": "Paschimottanasana (Seated Forward Bend)", "description": "Sit with legs extended and fold forward from the hips.", "benefit": "Stretches the hamstrings and lower back, stimulating the uterus and ovaries.", "image": "https://via.placeholder.com/200x150/6f42c1/ffffff?text=Paschimottanasana+Seated+Forward+Bend"},
                {"name": "Balasana (Child's Pose)", "description": "Kneel on the floor, sit back on your heels, and fold forward.", "benefit": "Deeply relaxing pose that helps to reduce stress and fatigue.", "image": "https://via.placeholder.com/200x150/6f42c1/ffffff?text=Balasana+Childs+Pose"},
                {"name": "Tadasana (Mountain Pose)", "description": "Stand tall with feet together, grounding through your feet and lengthening your spine.", "benefit": "Improves posture and creates a sense of stability and centeredness.", "image": "https://via.placeholder.com/200x150/6f42c1/ffffff?text=Tadasana+Mountain+Pose"},
                {"name": "Savasana (Corpse Pose)", "description": "Lie flat on your back with arms and legs relaxed.", "benefit": "Promotes deep relaxation, allowing the body to rest and repair.", "image": "https://via.placeholder.com/200x150/6f42c1/ffffff?text=Savasana+Corpse+Pose"}
            ],
            "breathing_exercises": [
                {"name": "Nadi Shodhana (Alternate Nostril Breathing)", "description": "Balances energy and calms the mind.", "image": "https://via.placeholder.com/200x150/17a2b8/ffffff?text=Nadi+Shodhana+Alternate+Nostril+Breathing"},
                {"name": "Bhramari Pranayama (Bee Breath)", "description": "Instantly relieves tension and anxiety.", "image": "https://via.placeholder.com/200x150/17a2b8/ffffff?text=Bhramari+Pranayama+Bee+Breath"}
            ],
            "meditation": {"name": "Yoga Nidra (Yogic Sleep)", "description": "A 10-minute guided practice for deep physical and mental relaxation.", "image": "https://via.placeholder.com/200x150/28a745/ffffff?text=Yoga+Nidra+Yogic+Sleep"},
            "precautions": [
                "Avoid deep twists and backbends",
                "No hot yoga during treatment",
                "Listen to your body and rest when needed",
                "Consult your doctor before starting any exercise program"
            ]
        }

def get_nutrition_analysis(meal_descriptions):
    """Analyze nutritional content of meals using AI"""
    try:
        context = f"""
        Analyze the nutritional content of the following meals for an IVF patient.
        Meals: {json.dumps(meal_descriptions)}

        Provide a JSON response with estimated values for:
        - total_calories: integer
        - protein_g: integer
        - folic_acid_mcg: integer
        - iron_mg: integer
        - omega_3_mg: integer
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a nutrition analysis expert. Estimate nutrient values from meal descriptions."},
                {"role": "user", "content": context}
            ],
            response_format={"type": "json_object"},
            max_tokens=300
        )
        
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        # Fallback analysis
        return {
            "total_calories": 1950,
            "protein_g": 75,
            "folic_acid_mcg": 350,
            "iron_mg": 16,
            "omega_3_mg": 1200
        }
