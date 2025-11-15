import pandas as pd
import numpy as np
import random

# ---------- IVF Success Prediction Dataset ----------
np.random.seed(42) # for reproducibility
n = 100

ivf_data = pd.DataFrame({
    "Age": np.random.randint(25, 45, n),
    "BMI": np.random.uniform(18, 35, n).round(2),
    "AMH": np.random.uniform(0.5, 6.0, n).round(2),
    "FSH": np.random.uniform(3.0, 12.0, n).round(2),
    "LH": np.random.uniform(2.0, 10.0, n).round(2),
    "Previous_IVF_Attempts": np.random.randint(0, 4, n),
    "Stress_Level": np.random.randint(1, 6, n),
    "Sleep_Hours": np.random.uniform(4, 9, n).round(1),
    "Exercise_Min_per_Day": np.random.randint(0, 60, n),
    "IVF_Success": np.random.choice([0, 1], n, p=[0.4, 0.6])  # 0=Fail, 1=Success
}) # 100 rows of IVF success data

# ---------- Mood & Wellness Trend Dataset ----------
dates = pd.date_range(start="2024-01-01", periods=100)
mood_data = pd.DataFrame({
    "Date": dates,
    "Mood_Rating": np.random.randint(1, 6, 100),
    "Stress_Level": np.random.randint(1, 6, 100),
    "Sleep_Hours": np.random.uniform(4, 9, 100).round(1),
    "Steps": np.random.randint(2000, 10000, 100)
})
mood_data["Next_Day_Mood"] = np.clip(
    mood_data["Mood_Rating"] - (mood_data["Stress_Level"] / 5) + np.random.normal(0, 0.5, 100), # some math
    1, 5
).round().astype(int)
 # 100 rows of mood data
# ---------- Emotion Analysis Dataset ---------- # 10 labels and text
texts = [
    "Feeling hopeful and calm today", "I’m very anxious about the next treatment",
    "Happy after doctor consultation", "Exhausted and sad from hormone shots",
    "Peaceful morning with meditation", "Nervous and scared about results",
    "Excited for the upcoming cycle", "Feeling down but trying to stay positive",
    "Relaxed after yoga", "Worried and tired"
]
labels = ["positive", "negative", "positive", "negative", "positive", "negative", "positive", "negative", "positive", "negative"]
emo_data = pd.DataFrame({"Text": np.random.choice(texts, 100), "Emotion": np.random.choice(labels, 100)}) # 100 rows of emotion data

# ---------- Save All ----------
with pd.ExcelWriter("ivf_datasets.xlsx") as writer:
    ivf_data.to_excel(writer, sheet_name="IVF_Success_Data", index=False) # save the IVF data
    mood_data.to_excel(writer, sheet_name="Mood_Wellness_Data", index=False)
    emo_data.to_excel(writer, sheet_name="Emotion_Data", index=False)

print("✅ IVF datasets saved as ivf_datasets.xlsx with 3 sheets!")