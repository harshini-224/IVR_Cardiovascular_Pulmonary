from sqlalchemy.orm import Session
from models import Patient, IVRLog
from datetime import datetime

# --- PATIENT MANAGEMENT ---

def create_patient(db: Session, data: dict):
    """Adds a new patient or returns existing one if phone matches."""
    existing = db.query(Patient).filter(Patient.phone == data["phone"]).first()
    if existing:
        return existing
    patient = Patient(**data)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

def get_patients(db: Session):
    """Returns all patients that haven't been deleted/deactivated."""
    return db.query(Patient).filter(Patient.active == True).all()

def get_patient_by_id(db: Session, pid: int):
    """Helper to find a patient by their primary key."""
    return db.query(Patient).filter(Patient.id == pid).first()

def update_patient_note(db: Session, pid: int, note: str):
    """Saves the doctor's assessment and marks the patient as reviewed."""
    patient = db.query(Patient).filter(Patient.id == pid).first()
    if patient:
        patient.override_notes = note
        patient.doctor_override = True
        db.commit()
        db.refresh(patient)
    return patient

# --- IVR & SYMPTOM LOGGING ---

def create_initial_log(db: Session, patient_id: int):
    """Creates a blank log entry at the start of a call."""
    new_log = IVRLog(
        patient_id=patient_id,
        symptoms={},  # Initialized as empty JSON
        risk=0.0,
        created_at=datetime.utcnow()
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

def update_ivr_answer(db: Session, patient_id: int, field: str, answer: str):
    """Updates the JSON symptoms dictionary with a new Yes/No answer."""
    log = db.query(IVRLog).filter(IVRLog.patient_id == patient_id).order_by(IVRLog.created_at.desc()).first()
    if log:
        # We must copy the dict to trigger SQLAlchemy's change tracking for JSON
        current_symptoms = dict(log.symptoms) if log.symptoms else {}
        current_symptoms[field] = answer
        log.symptoms = current_symptoms
        db.commit()
    return log

def finalize_risk_score(db: Session, patient_id: int, risk_score: float):
    """Saves the final calculated risk percentage (0.0 to 1.0)."""
    log = db.query(IVRLog).filter(IVRLog.patient_id == patient_id).order_by(IVRLog.created_at.desc()).first()
    if log:
        log.risk = risk_score
        db.commit()

def get_latest_log(db: Session, patient_id: int):
    """Fetches the most recent check-in for the Streamlit dashboard."""
    return db.query(IVRLog).filter(IVRLog.patient_id == patient_id).order_by(IVRLog.created_at.desc()).first()
