import pandas as pd
import numpy as np

# Weights based on AHA (Heart Failure/ACS) and WHO (Respiratory/Sepsis) protocols
CLINICAL_WEIGHTS = {
    # --- CARDIOVASCULAR (AHA Standards) ---
    "chest_discomfort": 0.85,    # AHA: Potential Acute Coronary Syndrome
    "dizziness": 0.70,           # AHA: Sign of low cardiac output
    "shortness_of_breath": 0.65, # AHA: Hallmark of worsening Heart Failure
    "weight_gain": 0.50,         # AHA: Objective measure of fluid overload
    "leg_swelling": 0.40,        # AHA: Peripheral edema
    "palpitations": 0.35,        # AHA: Potential arrhythmia
    "fatigue": 0.20,             # AHA: Non-specific HF sign

    # --- PULMONARY (WHO Standards) ---
    "rest_dyspnea": 0.80,        # WHO: Critical respiratory distress
    "chest_tightness": 0.60,     # WHO: Potential bronchospasm
    "exertional_dyspnea": 0.55,  # WHO: Functional decline
    "wheezing": 0.45,            # WHO: Obstructive airway sign
    "phlegm_change": 0.30,       # WHO: Bacterial infection indicator
    "cough_increase": 0.25,      # WHO: General irritation

    # --- GENERAL (WHO qSOFA/Sepsis Standards) ---
    "confusion": 0.90,           # WHO/qSOFA: Altered mental status (Critical)
    "fever_chills": 0.60,        # WHO: Systemic infection indicator
    "condition_worsened": 0.50,  # Subjective decline
    "nausea_vomiting": 0.30,     # Potential drug toxicity
    "new_pain": 0.25             
}

def calculate_risk_and_shap(disease_track, symptoms_dict):
    """
    Calculates track-specific risk and SHAP values.
    Each track is now strictly independent.
    """
    total_score = 0
    shap_explanations = {}

    # Define strictly separate features
    cardio_features = [
        "chest_discomfort", "dizziness", "shortness_of_breath", 
        "weight_gain", "leg_swelling", "palpitations"
    ]
    
    pulmonary_features = [
        "rest_dyspnea", "chest_tightness", "exertional_dyspnea", 
        "wheezing", "phlegm_change", "cough_increase"
    ]
    
    general_features = [
        "confusion", "fever_chills", "condition_worsened", 
        "nausea_vomiting", "new_pain", "fatigue"
    ]

    # 1. Strictly assign relevant keys—no combinations
    if disease_track == "Cardiovascular":
        relevant_keys = cardio_features
    elif disease_track == "Pulmonary":
        relevant_keys = pulmonary_features
    else:
        # This handles the "General" track specifically
        relevant_keys = general_features

    # 2. Calculate score based ONLY on relevant keys
    for field in relevant_keys:
        weight = CLINICAL_WEIGHTS.get(field, 0.0)
        answer = symptoms_dict.get(field)
        
        if answer == "Yes":
            total_score += weight
            shap_explanations[field] = weight
        else:
            shap_explanations[field] = 0.0

    # 3. Scaling: Keep the 2.5 threshold
    risk_percentage = min(max((total_score / 2.5) * 100, 0), 100)

    return round(risk_percentage, 2), shap_explanations

