from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified # Required for JSON updates
import models
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

def get_patient_by_id(db: Session, pid: int):
    """Helper to find a patient by their primary key."""
    return db.query(models.Patient).filter(models.Patient.id == pid).first()

def get_patients(db: Session):
    """Returns all active patients for the dashboard."""
    return db.query(Patient).filter(Patient.active == True).all()

def update_patient_note(db: Session, pid: int, note: str):
    """Saves the doctor's assessment notes to the patient record."""
    patient = db.query(Patient).filter(Patient.id == pid).first()
    if patient:
        patient.override_notes = note
        patient.doctor_override = True
        db.commit()
        db.refresh(patient)
    return patient

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
    """Creates a blank log entry at the start of a call."""
    new_log = IVRLog(
        patient_id=patient_id,
        symptoms={}, 
        shap={},
        risk_score=0.0,
        created_at=datetime.utcnow()
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

def update_ivr_answer(db: Session, patient_id: int, field: str, answer: str):
    """
    Updates the JSON symptoms dictionary. 
    Uses flag_modified to ensure Postgres saves the change.
    """
    log = db.query(IVRLog).filter(
        IVRLog.patient_id == patient_id
    ).order_by(IVRLog.created_at.desc()).first()
    
    if log:
        # Create a copy to ensure reference change
        current_symptoms = dict(log.symptoms) if log.symptoms else {}
        current_symptoms[field] = answer
        log.symptoms = current_symptoms
        
        # Manually trigger the "dirty" flag for the JSON column
        flag_modified(log, "symptoms")
        
        db.commit()
        db.refresh(log)
    return log

def get_latest_log(db: Session, patient_id: int):
    """Fetches the most recent log for risk calculation."""
    return db.query(IVRLog).filter(
        IVRLog.patient_id == patient_id
    ).order_by(IVRLog.created_at.desc()).first()

def get_all_logs(db: Session, patient_id: int):
    """Fetches the full 30-day history for a patient."""
    return db.query(IVRLog).filter(
        IVRLog.patient_id == patient_id
    ).order_by(IVRLog.created_at.asc()).all()

def finalize_risk_score(db: Session, patient_id: int, risk_score: float, shap_data: dict):
    # Fetch the current log being filled
    log = db.query(IVRLog).filter(
        IVRLog.patient_id == patient_id
    ).order_by(IVRLog.created_at.desc()).first()
    
    if log:
        log.risk_score = risk_score
        log.shap = shap_data  # This stores the weights for the bar chart
        
        # Crucial: tell SQLAlchemy to update the JSON field in the DB
        flag_modified(log, "shap")
        db.commit()
        db.refresh(log)
    return log
