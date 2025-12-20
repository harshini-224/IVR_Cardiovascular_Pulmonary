from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    disease = Column(String, nullable=False)
    enrolled_on = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True, index=True)
    doctor_override = Column(Boolean, default=False)
    override_notes = Column(String, nullable=True)

    # Optional: backref for logs
    ivr_logs = relationship("IVRLog", back_populates="patient")

class IVRLog(Base):
    __tablename__ = "ivr_logs"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    transcript = Column(String)
    symptoms = Column(JSON)
    risk = Column(Float)
    shap = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Optional: relationship back to patient
    patient = relationship("Patient", back_populates="ivr_logs")
