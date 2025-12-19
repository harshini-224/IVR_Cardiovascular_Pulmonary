import streamlit as st
import requests
from datetime import date

BACKEND = "https://ivr-backend-te24.onrender.com"

st.title("🫀 Cardio-Pulmonary Monitoring Dashboard")

# ---- ADD PATIENT ----
st.header("Enroll Patient")

with st.form("add"):
    name = st.text_input("Name")
    phone = st.text_input("Phone (+E.164)")
    diagnosis = st.selectbox("Diagnosis", ["Cardiovascular", "Pulmonary", "Both"])
    start = st.date_input("Start", date.today())
    end = st.date_input("End")

    if st.form_submit_button("Enroll"):
        requests.post(
            f"{BACKEND}/patients",
            data={
                "name": name,
                "phone": phone,
                "diagnosis": diagnosis,
                "start_date": start,
                "end_date": end
            }
        )
        st.success("Patient added")

# ---- LIST PATIENTS ----
st.header("Patients")

patients = requests.get(f"{BACKEND}/patients").json()

for p in patients:
    with st.expander(p["name"]):
        st.write(p)
        if st.button("Delete", key=p["id"]):
            requests.delete(f"{BACKEND}/patients/{p['id']}")
            st.experimental_rerun()

        if st.button("View IVR Logs", key=f"log{p['id']}"):
            logs = requests.get(f"{BACKEND}/ivr/{p['id']}").json()
            st.json(logs)
