from fastapi import FastAPI, Form
from database import SessionLocal, engine
from models import Base, Patient, IVRLog
from datetime import date
import json

Base.metadata.create_all(bind=engine)

app = FastAPI()

# -------- PATIENT CRUD --------

@app.post("/patients")
def add_patient(
    name: str = Form(...),
    phone: str = Form(...),
    diagnosis: str = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...)
):
    db = SessionLocal()
    p = Patient(
        name=name,
        phone=phone,
        diagnosis=diagnosis,
        start_date=start_date,
        end_date=end_date
    )
    db.add(p)
    db.commit()
    return {"status": "added"}

@app.get("/patients")
def list_patients():
    db = SessionLocal()
    return db.query(Patient).all()

@app.delete("/patients/{pid}")
def delete_patient(pid: int):
    db = SessionLocal()
    db.query(Patient).filter(Patient.id == pid).delete()
    db.commit()
    return {"status": "deleted"}

# -------- IVR LOGS --------

@app.post("/ivr/update")
def save_ivr(
    patient_id: int = Form(...),
    transcript: str = Form(...),
    symptoms: str = Form(...),
    followups: str = Form(...),
    risk: float = Form(...)
):
    db = SessionLocal()
    log = IVRLog(
        patient_id=patient_id,
        transcript=transcript,
        symptoms=symptoms,
        followups=followups,
        risk=risk
    )
    db.add(log)
    db.commit()
    return {"status": "saved"}

@app.get("/ivr/{pid}")
def ivr_logs(pid: int):
    db = SessionLocal()
    return db.query(IVRLog).filter(IVRLog.patient_id == pid).all()
