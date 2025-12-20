import streamlit as st
import requests

BACKEND = st.secrets["BACKEND_URL"]

st.title("Doctor Dashboard – Post Discharge Monitoring")

st.header("Enroll Patient")
name = st.text_input("Name")
phone = st.text_input("Phone (+91...)")
disease = st.selectbox("Disease", ["Cardiovascular", "Pulmonary"])

if st.button("Enroll"):
    r = requests.post(f"{BACKEND}/patients", json={
        "name": name,
        "phone": phone,
        "disease": disease
    })
    if r.status_code == 200:
        st.success("Patient enrolled")
    else:
        st.error(r.text)

st.header("Active Patients")

def fetch_patients():
    try:
        r = requests.get(f"{BACKEND}/patients", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Backend error: {e}")
        return []

patients = fetch_patients()

for p in patients:
    st.write(f"{p['name']} — {p['phone']} — {p['disease']}")
    if st.button(f"📞 Call {p['name']}"):
        r = requests.post(f"{BACKEND}/call/{p['phone']}")
        if r.status_code == 200:
            st.success("Call initiated")
        else:
            st.error(r.text)
