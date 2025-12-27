from sqlalchemy.orm import Session
import models
from models import Patient, IVRLog
from datetime import datetime

# --- PATIENT MANAGEMENT ---

def create_patient(db: Session, data: dict):
    """Adds a new patient or returns existing one if phone matches."""
    existing = db.query(Patient).filter(Patient.phone == data["phone"]).first() #
    if existing:
        return existing #
    patient = Patient(**data) #
    db.add(patient) #
    db.commit() #
    db.refresh(patient) #
    return patient #

# Add this to crud.py
def get_patient_by_id(db: Session, pid: int):
    """Helper to find a patient by their primary key."""
    return db.query(models.Patient).filter(models.Patient.id == pid).first()

def get_patients(db: Session):
    """Returns all active patients for the dashboard."""
    return db.query(Patient).filter(Patient.active == True).all() #

def update_patient_note(db: Session, pid: int, note: str):
    """Saves the doctor's assessment notes to the patient record."""
    patient = db.query(Patient).filter(Patient.id == pid).first() #
    if patient:
        patient.override_notes = note #
        patient.doctor_override = True #
        db.commit() #
        db.refresh(patient) #
    return patient #

def delete_patient(db: Session, pid: int):
    """Permanently deletes a patient and all their history via cascade."""
    patient = db.query(Patient).filter(Patient.id == pid).first() #
    if patient:
        db.delete(patient) #
        db.commit() #
        return True #
    return False #

# --- IVR & MONITORING HISTORY ---

def create_initial_log(db: Session, patient_id: int):
    """Creates a blank log entry at the start of a call."""
    new_log = IVRLog(
        patient_id=patient_id, #
        symptoms={}, #
        risk_score=0.0, #
        created_at=datetime.utcnow() #
    )
    db.add(new_log) #
    db.commit() #
    db.refresh(new_log) #
    return new_log #

def get_all_logs(db: Session, patient_id: int):
    """
    Fetches the full 30-day history for a patient.
    Ordered by date so you can see Day 1, Day 2, etc.
    """
    return db.query(IVRLog).filter(
        IVRLog.patient_id == patient_id
    ).order_by(IVRLog.created_at.asc()).all() #

def finalize_risk_score(db: Session, patient_id: int, risk_score: float):
    """Saves the final calculated risk percentage (0 to 100)."""
    # Finds the current active log to update it
    log = db.query(IVRLog).filter(
        IVRLog.patient_id == patient_id
    ).order_by(IVRLog.created_at.desc()).first() #
    if log:
        log.risk_score = risk_score #
        db.commit() #
