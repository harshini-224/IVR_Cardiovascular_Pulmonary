from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
import models
from models import Patient, IVRLog
from datetime import datetime

# --- PATIENT MANAGEMENT ---

def create_patient(db: Session, data: dict):
    """Adds a new patient or returns existing one if phone_number matches."""
    # Updated to use 'phone_number' to match schemas.py
    existing = db.query(Patient).filter(Patient.phone_number == data["phone_number"]).first()
    if existing:
        return existing
    patient = Patient(**data)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

def get_patient_by_id(db: Session, pid: int):
    """Helper to find a patient by their primary key."""
    return db.query(models.Patient).filter(models.Patient.id == pid).first()

def get_patients(db: Session):
    """Returns all active patients for the dashboard."""
    return db.query(Patient).filter(Patient.active == True).all()

def delete_patient(db: Session, pid: int):
    """Permanently deletes a patient and all their history via cascade."""
    patient = db.query(Patient).filter(Patient.id == pid).first()
    if patient:
        db.delete(patient)
        db.commit()
        return True
    return False

# --- IVR & MONITORING HISTORY ---

def create_initial_log(db: Session, patient_id: int):
    """Creates a blank log entry at the start of a call with 'Pending' status."""
    new_log = IVRLog(
        patient_id=patient_id,
        symptoms={}, 
        shap={},
        risk_score=0.0,
        doctor_status="Pending",  # Essential for dashboard filtering
        created_at=datetime.utcnow()
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

def update_ivr_answer(db: Session, patient_id: int, field: str, answer: str):
    """Updates the JSON symptoms dictionary dynamically."""
    log = db.query(IVRLog).filter(
        IVRLog.patient_id == patient_id
    ).order_by(IVRLog.created_at.desc()).first()
    
    if log:
        current_symptoms = dict(log.symptoms) if log.symptoms else {}
        current_symptoms[field] = answer
        log.symptoms = current_symptoms
        flag_modified(log, "symptoms")
        db.commit()
    return log

def finalize_risk_score(db: Session, patient_id: int, risk_score: float, shap_data: dict):
    """Saves final ML results and SHAP weights after the IVR ends."""
    log = db.query(IVRLog).filter(
        IVRLog.patient_id == patient_id
    ).order_by(IVRLog.created_at.desc()).first()
    
    if log:
        log.risk_score = risk_score
        log.shap = shap_data
        flag_modified(log, "shap")
        db.commit()
        db.refresh(log)
    return log

# --- DOCTOR-IN-THE-LOOP (VERIFICATION) ---

def update_log_status(db: Session, log_id: int, status: str, notes: str):
    """
    Updates a specific log with the physician's verification.
    This fulfills clinical explainability and audit trail requirements.
    """
    log = db.query(IVRLog).filter(IVRLog.id == log_id).first()
    if log:
        log.doctor_status = status
        log.doctor_notes = notes
        log.reviewed_at = datetime.utcnow()
        db.commit()
        db.refresh(log)
        return log
    return None

def get_all_logs(db: Session, patient_id: int):
    """Fetches full check-in history, sorted by newest first for the dashboard."""
    return db.query(IVRLog).filter(
        IVRLog.patient_id == patient_id
    ).order_by(IVRLog.created_at.desc()).all()
