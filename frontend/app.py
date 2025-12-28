import streamlit as st
import requests
import os
import pandas as pd
import matplotlib.pyplot as plt

# Backend URL configuration
BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Doctor Monitoring Dashboard", layout="wide", page_icon="🏥")

# --- CLINICAL REFERENCE MAP (The "What" and "Source") ---
CLINICAL_REF = {
    "chest_discomfort": {"name": "Acute Chest Discomfort", "src": "AHA ACS Guidelines"},
    "leg_swelling": {"name": "Peripheral Edema", "src": "AHA Heart Failure Protocol"},
    "confusion": {"name": "Altered Mental Status", "src": "WHO qSOFA (Sepsis)"},
    "shortness_of_breath": {"name": "Dyspnea", "src": "AHA/WHO Standards"},
    "weight_gain": {"name": "Rapid Fluid Retention", "src": "AHA HF Red Flags"},
    "fever_chills": {"name": "Febrile Response", "src": "WHO Infection Protocol"},
    "rest_dyspnea": {"name": "Resting Respiratory Distress", "src": "WHO Critical Care"},
    "wheezing": {"name": "Bronchospasm", "src": "ATS Pulmonary Standards"}
}

# --- CUSTOM UI STYLING ---
# --- CUSTOM UI STYLING ---
st.markdown("""
    <style>
    .risk-high { color: #ff4b4b; font-size: 18px; font-weight: bold; }
    .risk-med { color: #ffa500; font-size: 18px; font-weight: bold; }
    .risk-low { color: #008000; font-size: 18px; font-weight: bold; }
    
    .day-card { 
        border: 1px solid #e6e9ef; padding: 20px; border-radius: 10px; 
        background-color: #f9f9f9; margin-bottom: 15px;
    }
    
    /* Updated for Black Text and better contrast */
    .explanation-box {
        background-color: #fdfdfd; 
        border-left: 5px solid #ff4b4b;
        border-top: 1px solid #eee;
        border-right: 1px solid #eee;
        border-bottom: 1px solid #eee;
        padding: 15px; 
        margin-top: 10px; 
        border-radius: 5px;
        color: #000000; /* Set font color to black */
    }
    
    .explanation-box strong {
        color: #000000; /* Ensure bold headers are black */
        font-size: 1.1rem;
    }
    
    .explanation-box small {
        color: #333333; /* Dark gray for source text */
        display: block;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Patient Monitoring & Risk Dashboard")

# --- SIDEBAR: ENROLLMENT ---
with st.sidebar:
    st.header("📋 Patient Enrollment")
    with st.form("enrollment_form", clear_on_submit=True):
        name = st.text_input("Full Name")
        phone = st.text_input("Phone Number")
        # Updated to match disease_track in backend
        track = st.selectbox("Disease Track", ["Cardiovascular", "Pulmonary","General"])
        
        if st.form_submit_button("Enroll Patient"):
            payload = {"name": name, "phone_number": phone, "disease_track": track}
            res = requests.post(f"{BACKEND}/patients", json=payload)
            if res.status_code == 200:
                st.success(f"Enrolled {name}")
                st.rerun()

# --- MAIN MONITORING SECTION ---
def fetch_patients():
    try:
        r = requests.get(f"{BACKEND}/patients")
        return r.json() if r.status_code == 200 else []
    except: return []

patients = fetch_patients()

for p in patients:
    # Patient Expander Header
    with st.expander(f"👤 {p['name']} | Track: {p['disease_track']} | Status: {'Active' if p['active'] else 'Inactive'}"):
        col_actions, col_history = st.columns([1, 2])
        
        with col_actions:
            st.markdown("### Actions")
            if st.button(f"📞 Trigger Call", key=f"call_{p['id']}"):
                requests.post(f"{BACKEND}/call/{p['phone_number']}?patient_id={p['id']}")
                st.toast("Call Triggered")
            
            if st.button(f"🗑️ Delete", key=f"del_{p['id']}"):
                requests.delete(f"{BACKEND}/patients/{p['id']}")
                st.rerun()

        with col_history:
            st.markdown("### 30-Day Check-in History")
            log_res = requests.get(f"{BACKEND}/patients/{p['id']}/all-logs")
            
            if log_res.status_code == 200:
                logs = log_res.json()
                for log in reversed(logs):
                    score = log.get("risk_score", 0)
                    
                    st.markdown("<div class='day-card'>", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns([1, 1, 2])
                    
                    c1.metric("Risk Score", f"{score}%")
                    
                    # Risk Level Badge
                    if score > 60: c2.markdown("<span class='risk-high'>🚨 HIGH</span>", unsafe_allow_html=True)
                    elif score > 30: c2.markdown("<span class='risk-med'>⚠️ MED</span>", unsafe_allow_html=True)
                    else: c2.markdown("<span class='risk-low'>✅ STABLE</span>", unsafe_allow_html=True)

                    if c3.button("Analyze Risk Drivers", key=f"analyze_{log['id']}"):
                        st.write("---")
                        
                        # 1. SHAP GRAPH (RED BARS ONLY)
                        shap_data = log.get("shap", {})
                        # Filter out non-positive values (Removes -0.1 and 0.0)
                        active_drivers = {k: v for k, v in shap_data.items() if v > 0}
                        
                        if active_drivers:
                            st.write("#### 🧠 Clinical Risk Drivers")
                            
                            # Professional Matplotlib Chart
                            fig, ax = plt.subplots(figsize=(6, len(active_drivers)*0.5))
                            # Sort by weight
                            sorted_drivers = dict(sorted(active_drivers.items(), key=lambda x: x[1]))
                            ax.barh(list(sorted_drivers.keys()), list(sorted_drivers.values()), color='#ff4b4b')
                            ax.set_title("Impact Weight per Symptom")
                            st.pyplot(fig)

                            # 2. PERFECT EXPLAINABILITY TEXT (WHAT & SOURCE)
                            st.write("#### 📋 Medical Justification")
                            # Inside the "Analyze Risk Drivers" button logic
                            for symptom, weight in active_drivers.items():
                                ref = CLINICAL_REF.get(symptom, {"name": symptom.replace("_", " ").title(), "src": "Standard Clinical Protocol"})
    
                                st.markdown(f"""
                                <div class='explanation-box'>
                                    <strong>{ref['name']}</strong> (+{weight} impact weight)
                                    <p style="color: black; margin-top: 5px;">
                                        This symptom was identified as a driver for the current risk score based on the patient's response.
                                    </p>
                                    <small>Source: {ref['src']}</small>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.success("No active risk drivers detected for this log.")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
