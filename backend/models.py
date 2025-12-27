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
    
    # Clinical Review Fields
    doctor_override = Column(Boolean, default=False)
    override_notes = Column(String, nullable=True) # This is where your Assessment saves

    # Relationship to allow multiple logs (Day 1, Day 2, etc.)
    ivr_logs = relationship("IVRLog", back_populates="patient", cascade="all, delete-orphan")

class IVRLog(Base):
    __tablename__ = "ivr_logs"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    
    transcript = Column(String, nullable=True) 
    symptoms = Column(JSON, default={}) 
    risk_score = Column(Float, default=0.0) # We use risk_score (0-100)
    shap = Column(JSON, nullable=True) 
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="ivr_logs")
