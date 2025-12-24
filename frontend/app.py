import streamlit as st
import requests
import os
import pandas as pd

# Configure Backend URL - This should point to your FastAPI service on Render
BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Doctor Monitoring Dashboard", layout="wide", page_icon="🏥")

# Custom CSS for a clean medical look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { border-radius: 20px; }
    .risk-high { color: #ff4b4b; font-weight: bold; }
    .risk-med { color: #ffa500; font-weight: bold; }
    .risk-low { color: #008000; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Patient Monitoring & Risk Dashboard")
st.info("Automated IVR Check-ins: Real-time data from Cardiovascular & Pulmonary patients.")

# --- SIDEBAR: PATIENT ENROLLMENT ---
with st.sidebar:
    st.header("Register New Patient")
    with st.form("enrollment_form"):
        name = st.text_input("Patient Full Name")
        phone = st.text_input("Phone Number (with +country code)")
        disease = st.selectbox("Disease Track", ["Cardiovascular", "Pulmonary"])
        submit = st.form_submit_button("Enroll in 30-Day Program")
        
        if submit:
            if name and phone:
                try:
                    res = requests.post(f"{BACKEND}/patients", json={
                        "name": name, "phone": phone, "disease": disease
                    })
                    if res.status_code == 200:
                        st.success(f"Successfully enrolled {name}")
                    else:
                        st.error(f"Enrollment failed: {res.text}")
                except Exception as e:
                    st.error(f"Could not connect to backend: {e}")
            else:
                st.warning("All fields are required.")

# --- MAIN SECTION: PATIENT RISK MONITORING ---

def get_all_patients():
    try:
        r = requests.get(f"{BACKEND}/patients")
        return r.json() if r.status_code == 200 else []
    except:
        return []

patients = get_all_patients()

if not patients:
    st.write("### No patients currently enrolled.")
else:
    st.write(f"### Monitoring {len(patients)} Active Patients")
    
    for p in patients:
        # Create an expander for each patient to keep the UI clean
        with st.expander(f"👤 {p['name']} | Track: {p['disease']} | Phone: {p['phone']}"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.write("**Patient Details**")
                st.write(f"📅 Enrolled: {p['enrolled_on'][:10]}")
                st.write(f"Status: {'✅ Reviewed' if p['doctor_override'] else '⏳ Awaiting Review'}")
                
                # Manual Trigger Button
                if st.button(f"📞 Trigger Call Now", key=f"call_{p['id']}"):
                    requests.post(f"{BACKEND}/call/{p['phone']}?patient_id={p['id']}")
                    st.toast(f"Call sent to {p['name']}")

            with col2:
                # Fetch the latest IVR log from the backend
                log_res = requests.get(f"{BACKEND}/patients/{p['id']}/latest-log")
                
                if log_res.status_code == 200:
                    log = log_res.json()
                    symptoms = log.get("symptoms", {})
                    risk_score = log.get("risk", 0.0)

                    # 1. RISK LEVEL DISPLAY
                    if risk_score >= 0.7:
                        st.error(f"🚨 HIGH RISK ({int(risk_score*100)}%)")
                        # Explainability Logic
                        yes_symptoms = [k.replace('_', ' ').title() for k, v in symptoms.items() if v == "Yes"]
                        st.markdown(f"**Explainability:** Critical symptoms reported: *{', '.join(yes_symptoms)}*")
                    elif risk_score >= 0.4:
                        st.warning(f"⚠️ MODERATE RISK ({int(risk_score*100)}%)")
                    else:
                        st.success(f"✅ STABLE / LOW RISK ({int(risk_score*100)}%)")

                    # 2. SYMPTOM TABLE
                    if symptoms:
                        st.write("**Check-in Responses:**")
                        df = pd.DataFrame(symptoms.items(), columns=["Question", "Response"])
                        st.table(df)
                    
                    # 3. CLINICAL NOTES SECTION
                    st.write("**Doctor's Assessment:**")
                    current_note = p.get("override_notes", "")
                    note_input = st.text_area("Observations:", value=current_note if current_note else "", key=f"note_{p['id']}")
                    
                    if st.button("Save Assessment", key=f"btn_note_{p['id']}"):
                        save_res = requests.put(f"{BACKEND}/patients/{p['id']}/note", json={"note": note_input})
                        if save_res.status_code == 200:
                            st.success("Note saved.")
                            st.rerun()
                else:
                    st.info("No check-in data available yet. An automated call will trigger daily at 10 AM.")

st.divider()
st.caption("AI-Powered Post-Discharge System | Created for 2025 Clinical Standards")
