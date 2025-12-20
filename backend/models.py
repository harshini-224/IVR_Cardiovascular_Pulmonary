from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey
from datetime import datetime
from database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    disease = Column(String, nullable=False)
    enrolled_on = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True, index=True)
    doctor_override = Column(Boolean, default=False)
    override_notes = Column(String, nullable=True)

class IVRLog(Base):
    __tablename__ = "ivr_logs"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    transcript = Column(String)
    symptoms = Column(JSON)
    risk = Column(Float)
    shap = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
