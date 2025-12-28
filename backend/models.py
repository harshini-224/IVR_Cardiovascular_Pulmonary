from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

# Import Base from your database file
# If database.py is in the same folder, use .database
try:
    from .database import Base
except ImportError:
    from database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    disease_track = Column(String, nullable=False) 
    enrolled_on = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True, index=True)
    
    doctor_override = Column(Boolean, default=False)
    override_notes = Column(String, nullable=True)

    # Relationship to allow multiple logs
    ivr_logs = relationship("IVRLog", back_populates="owner", cascade="all, delete-orphan")

class IVRLog(Base):
    __tablename__ = "ivr_logs"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    symptoms = Column(JSON)
    shap = Column(JSON)
    risk_score = Column(Float)
    
    doctor_status = Column(String, default="Pending")
    doctor_notes = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # FIXED: This now matches 'ivr_logs' in the Patient class
    owner = relationship("Patient", back_populates="ivr_logs")
