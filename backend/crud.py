from sqlalchemy.orm import Session
from models import Patient

def create_patient(db: Session, data: dict):
    existing = db.query(Patient).filter(Patient.phone == data["phone"]).first()
    if existing:
        return existing
    patient = Patient(**data)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

def get_patients(db: Session):
    return db.query(Patient).filter(Patient.active == True).all()

def delete_patient(db: Session, pid: int):
    patient = db.query(Patient).filter(Patient.id == pid).first()
    if patient:
        patient.active = False
        db.commit()
