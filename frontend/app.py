import streamlit as st
import requests
import os
import pandas as pd
from datetime import datetime

# Backend URL configuration
BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Doctor Monitoring Dashboard", layout="wide", page_icon="🏥")

# --- CUSTOM UI STYLING ---
st.markdown("""
    <style>
    .risk-high { color: #ff4b4b; font-size: 18px; font-weight: bold; }
    .risk-med { color: #ffa500; font-size: 18px; font-weight: bold; }
    .risk-low { color: #008000; font-size: 18px; font-weight: bold; }
    .day-card { 
        border: 1px solid #e6e9ef; 
        padding: 15px; 
        border-radius: 10px; 
        background-color: #ffffff; 
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .stExpander { border: 1px solid #d1d5db !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Patient Monitoring & Risk Dashboard")

# --- SIDEBAR: ENROLLMENT ---
with st.sidebar:
    st.header("📋 Patient Enrollment")
    st.info("Register a patient to begin their 30-day automated monitoring track.")
    
    with st.form("enrollment_form", clear_on_submit=True):
        name = st.text_input("Full Name")
        phone = st.text_input("Phone Number (+...)")
        disease = st.selectbox("Disease Track", ["Cardiovascular", "Pulmonary"])
        
        if st.form_submit_button("Enroll Patient"):
            if name and phone:
                try:
                    payload = {"name": name, "phone": phone, "disease": disease}
                    res = requests.post(f"{BACKEND}/patients", json=payload)
                    if res.status_code == 200:
                        st.success(f"Successfully enrolled {name}")
                        st.rerun()
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")
            else:
                st.warning("Please fill in all fields.")

# --- MAIN SECTION: MONITORING ---

def get_patients():
    try:
        r = requests.get(f"{BACKEND}/patients")
        return r.json() if r.status_code == 200 else []
    except:
        return []

patients = get_patients()

if not patients:
    st.info("No active patients. Use the sidebar to enroll a new patient.")
else:
    st.subheader(f"Monitoring {len(patients)} Active Cases")
    
    for p in patients:
        # Create an expander with colored status based on most recent log if exists
        with st.expander(f"👤 {p['name']} | Track: {p['disease']} | Phone: {p['phone']}"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("### Patient Actions")
                
                # Manual Call Trigger
                if st.button(f"📞 Trigger Call Now", key=f"call_{p['id']}"):
                    requests.post(f"{BACKEND}/call/{p['phone']}?patient_id={p['id']}")
                    st.toast(f"Outbound call sent to {p['name']}")
                
                # Delete/Discharge Patient
                if st.button(f"🗑️ Discharge Patient", key=f"del_{p['id']}"):
                    requests.delete(f"{BACKEND}/patients/{p['id']}")
                    st.success("Patient Discharged.")
                    st.rerun()
                
                st.divider()
                
                # Clinical Assessment (Saves to override_notes)
                st.markdown("### Clinical Assessment")
                

            with col2:
                st.markdown("### 30-Day History")
                # Use .get() to avoid KeyErrors if the field is null
                current_note = p.get("override_notes", "") 
    
    # Display the existing note so the doctor can see it
                if current_note:
                    st.info(f"**Current Note:** {current_note}")
                else:
                    st.write("*No assessment recorded yet.*")

                note_input = st.text_area("New Observations:", value=current_note, key=f"note_{p['id']}")
    
                if st.button("Save Assessment", key=f"btn_note_{p['id']}"):
                    res = requests.put(f"{BACKEND}/patients/{p['id']}/note", json={"note": note_input})
                    if res.status_code == 200:
                        st.success("Assessment saved!")
                        st.rerun() # Refresh the UI to show the new note
                # Fetch all logs for this specific patient
                log_res = requests.get(f"{BACKEND}/patients/{p['id']}/all-logs")
                
                if log_res.status_code == 200:
                    logs = log_res.json() # Returns a list ordered by date
                    
                    if not logs:
                        st.info("No check-in logs found yet. The first automated call will occur within 24 hours.")
                    else:
                        # Displaying logs from Newest to Oldest
                        for idx, log in enumerate(reversed(logs)):
                            day_num = len(logs) - idx
                            score = int(log.get("risk_score", 0))
                            
                            st.markdown(f"<div class='day-card'>", unsafe_allow_html=True)
                            c1, c2, c3 = st.columns([1, 2, 2])
                            
                            c1.metric(f"Day {day_num}", f"{score}%")
                            
                            if score > 60:
                                c2.markdown(f"<span class='risk-high'>🚨 HIGH RISK</span>", unsafe_allow_html=True)
                            elif score > 30:
                                c2.markdown(f"<span class='risk-med'>⚠️ MODERATE</span>", unsafe_allow_html=True)
                            else:
                                c2.markdown(f"<span class='risk-low'>✅ STABLE</span>", unsafe_allow_html=True)
                            
                            # ... (inside your log loop) ...

                            if c3.button("Show Responses", key=f"details_{log['id']}"):
    # 1. Show the raw answers in a table
                                st.write("#### Detailed Symptoms")
                                st.table(pd.DataFrame(log['symptoms'].items(), columns=["Question", "Response"]))
    
    # 2. ADD SHAP EXPLAINABILITY HERE
                                if log.get("shap"):
                                    st.write("#### 🧠 Clinical Explanation (SHAP)")
                                    st.info("Based on AHA/WHO weighted protocols. Red increases risk, Blue decreases risk.")
        
        # Convert SHAP dictionary to a DataFrame for plotting
                                    shap_df = pd.DataFrame(
                                        log["shap"].items(), 
                                        columns=["Feature", "Contribution"]
                                    ).sort_values(by="Contribution", ascending=True)
                                    
        # Create a horizontal bar chart
                                    st.bar_chart(data=shap_df, x="Feature", y="Contribution", color="#ff4b4b")
                                else:
                                    st.caption("SHAP explainability data not available for this log.")
                                
                            
                                st.markdown("</div>", unsafe_allow_html=True)
                            else:
                                st.error("Could not retrieve history.")

st.divider()
st.caption("AI-Powered Post-Discharge Monitoring System | Clinical Standard 2025")
