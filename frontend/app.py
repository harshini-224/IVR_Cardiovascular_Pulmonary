import streamlit as st
import requests
import os
import pandas as pd
from datetime import datetime

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Doctor Monitoring Dashboard", layout="wide", page_icon="🏥")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .risk-high { color: #ff4b4b; font-size: 20px; font-weight: bold; }
    .risk-med { color: #ffa500; font-size: 20px; font-weight: bold; }
    .risk-low { color: #008000; font-size: 20px; font-weight: bold; }
    .day-card { border: 1px solid #ddd; padding: 10px; border-radius: 10px; margin-bottom: 5px; background: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Patient Monitoring & Risk Dashboard")

# --- PATIENT RISK MONITORING ---
def get_all_patients():
    try:
        r = requests.get(f"{BACKEND}/patients")
        return r.json() if r.status_code == 200 else []
    except: return []

patients = get_all_patients()

if not patients:
    st.info("No patients currently enrolled.")
else:
    for p in patients:
        with st.expander(f"👤 {p['name']} | Track: {p['disease']} | ID: {p['id']}"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("Patient Status")
                # Trigger Call
                if st.button(f"📞 Trigger Call", key=f"call_{p['id']}"):
                    requests.post(f"{BACKEND}/call/{p['phone']}?patient_id={p['id']}")
                    st.toast("Call initiated.")
                
                # Doctor's Assessment (Saved to the Patient Table)
                st.write("**Clinical Notes**")
                current_note = p.get("discharge_summary", "") # Using existing field to store notes
                note_input = st.text_area("Observations:", value=current_note, key=f"note_{p['id']}")
                if st.button("Save Notes", key=f"btn_note_{p['id']}"):
                    requests.put(f"{BACKEND}/patients/{p['id']}/note", json={"note": note_input})
                    st.success("Notes updated.")

            with col2:
                # --- DAY TO DAY MONITORING ---
                st.subheader("30-Day Check-in History")
                
                # Fetch all logs for this patient (Ensure backend has an endpoint for all logs)
                log_res = requests.get(f"{BACKEND}/patients/{p['id']}/all-logs")
                
                if log_res.status_code == 200:
                    logs = log_res.json()
                    if not logs:
                        st.info("No check-in history found.")
                    else:
                        for idx, log in enumerate(reversed(logs)):
                            day_num = len(logs) - idx
                            risk_score = log.get("risk_score", 0.0)
                            
                            # Correct Risk Display (Assuming backend saves 0.0 to 1.0)
                            display_score = int(risk_score) 
                            
                            with st.container():
                                st.markdown(f"<div class='day-card'>", unsafe_allow_html=True)
                                c1, c2, c3 = st.columns([1, 2, 2])
                                c1.metric(f"Day {day_num}", f"{display_score}%")
                                
                                # Set Risk Category
                                if display_score > 60:
                                    c2.markdown(f"<span class='risk-high'>🚨 HIGH RISK</span>", unsafe_allow_html=True)
                                elif display_score > 30:
                                    c2.markdown(f"<span class='risk-med'>⚠️ MODERATE RISK</span>", unsafe_allow_html=True)
                                else:
                                    c2.markdown(f"<span class='risk-low'>✅ STABLE</span>", unsafe_allow_html=True)
                                
                                if c3.button("View Details", key=f"det_{log['id']}"):
                                    st.table(pd.DataFrame(log['symptoms'].items(), columns=["Question", "Response"]))
                                st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.error("Failed to load history.")

st.divider()
st.caption("AI-Powered Post-Discharge System | 2025 Standard")
