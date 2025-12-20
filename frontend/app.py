import streamlit as st
import requests
import os

BACKEND = os.environ["BACKEND_URL"]


st.title("Doctor Dashboard – Post Discharge Monitoring")

st.header("Enroll Patient")
name = st.text_input("Name")
phone = st.text_input("Phone (+91...)")
disease = st.selectbox("Disease", ["Cardiovascular", "Pulmonary"])

if st.button("Enroll"):
    requests.post(f"{BACKEND}/patients", json={
        "name": name,
        "phone": phone,
        "disease": disease
    })
    st.success("Patient enrolled")

st.header("Active Patients")
patients = requests.get(f"{BACKEND}/patients").json()

for p in patients:
    st.write(p["name"], p["phone"], p["disease"])
    if st.button(f"Call {p['name']}"):
        requests.post(f"{BACKEND}/call/{p['phone']}")
