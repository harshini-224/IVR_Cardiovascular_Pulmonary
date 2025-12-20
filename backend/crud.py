from sqlalchemy.orm import Session
from models import Patient, IVRLog

def create_patient(db: Session, data: dict):
    patient = Patient(**data)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

def get_patients(db: Session):
    return db.query(Patient).filter(Patient.active == True).all()

def get_patient(db: Session, pid: int):
    return db.query(Patient).filter(Patient.id == pid).first()

def delete_patient(db: Session, pid: int):
    patient = get_patient(db, pid)
    patient.active = False
    db.commit()

def log_ivr(db: Session, data: dict):
    log = IVRLog(**data)
    db.add(log)
    db.commit()
