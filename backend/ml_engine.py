import pandas as pd
import numpy as np
from sqlalchemy.orm.attributes import flag_modified

# Weights based on AHA (Heart Failure) and WHO (Sepsis/Respiratory) protocols
# Weights based on AHA (Heart Failure/ACS) and WHO (Respiratory/Sepsis) protocols
CLINICAL_WEIGHTS = {
    # --- CARDIOVASCULAR (AHA Standards) ---
    "chest_discomfort": 0.85,    # AHA: Potential Acute Coronary Syndrome (Highest Priority)
    "dizziness": 0.70,           # AHA: Sign of low cardiac output or arrhythmia
    "shortness_of_breath": 0.65, # AHA: Hallmark of worsening Heart Failure
    "weight_gain": 0.50,         # AHA: Objective measure of fluid overload (>3lbs in 2 days)
    "leg_swelling": 0.40,        # AHA: Peripheral edema (Heart Failure sign)
    "palpitations": 0.35,        # AHA: Potential arrhythmia
    "fatigue": 0.20,             # AHA: Non-specific but common in HF

    # --- PULMONARY (WHO Standards) ---
    "rest_dyspnea": 0.80,        # WHO: Critical respiratory distress
    "chest_tightness": 0.60,     # WHO: Potential bronchospasm or ACS overlap
    "exertional_dyspnea": 0.55,  # WHO: Functional decline
    "wheezing": 0.45,            # WHO: Obstructive airway sign
    "phlegm_change": 0.30,       # WHO: Indicator of bacterial infection/exacerbation
    "cough_increase": 0.25,      # WHO: General irritation/bronchitis

    # --- GENERAL (WHO qSOFA/Sepsis Standards) ---
    "confusion": 0.90,           # WHO/qSOFA: Altered mental status (Critical Red Flag)
    "fever_chills": 0.60,        # WHO: Indicator of systemic infection/Sepsis
    "condition_worsened": 0.50,  # Subjective but clinically significant functional decline
    "nausea_vomiting": 0.30,     # WHO: Potential electrolyte imbalance or drug toxicity
    "new_pain": 0.25             # General symptom tracking
}

def calculate_clinical_shap(symptoms_dict):
    """
    Calculates risk and SHAP values using AHA/WHO clinical weights.
    Returns: (risk_score, shap_explanations)
    """
    total_score = 0
    shap_explanations = {}

    for field, weight in CLINICAL_WEIGHTS.items():
        answer = symptoms_dict.get(field)
        
        if answer == "Yes":
            total_score += weight
            shap_explanations[field] = weight
        elif answer == "No":
            # Protective factor: subtracts from risk
            shap_explanations[field] = -0.1
        else:
            # Not applicable to this patient track
            shap_explanations[field] = 0.0

    # Scale: A score of ~2.5 total points indicates 100% risk in this clinical context
    risk_percentage = min(max((total_score / 2.5) * 100, 0), 100)

    return round(risk_percentage, 2), shap_explanations
