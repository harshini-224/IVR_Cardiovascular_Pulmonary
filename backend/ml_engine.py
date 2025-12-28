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
    - Removes -0.1 (No negative values).
    - Filters features based on the patient's medical track.
    """
    total_score = 0
    shap_explanations = {}

    # Define which features belong to which track
   # Ensure these EXACTLY match the 'field' names in main.py FRIENDLY_QUESTIONS
    cardio_features = [
        "shortness_of_breath", "leg_swelling", 
        "chest_discomfort", "weight_gain", "fatigue", "dizziness"
    ]
    
    pulmonary_features = [
        "exertional_dyspnea", "cough_increase", 
        "wheezing", "rest_dyspnea", "phlegm_change"
    ]
    
    general_features = [
        "fever_chills", "confusion", "condition_worsened"
    ]

    # 1. Determine relevant features for this specific patient
    if disease_track == "Cardiovascular":
        relevant_keys = cardio_features + general_features
    elif disease_track == "Pulmonary":
        relevant_keys = pulmonary_features + general_features
    else:
        relevant_keys = general_features

    # 2. Calculate impact ONLY for relevant features
    for field in relevant_keys:
        weight = CLINICAL_WEIGHTS.get(field, 0.0)
        answer = symptoms_dict.get(field)
        
        if answer == "Yes":
            total_score += weight
            shap_explanations[field] = weight
        else:
            # We set to 0.0 so it doesn't appear in the SHAP graph
            # This removes the -0.1 requirement
            shap_explanations[field] = 0.0

    # 3. Scale: Total score / 2.5 (Clinical Threshold)
    risk_percentage = min(max((total_score / 2.5) * 100, 0), 100)

    return round(risk_percentage, 2), shap_explanations
