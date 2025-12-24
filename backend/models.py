from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    
    # Stores 'Cardiovascular' or 'Pulmonary' to route IVR questions
    disease = Column(String, nullable=False) 
    enrolled_on = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True, index=True)
    
    # Clinical Review Fields
    doctor_override = Column(Boolean, default=False)
    override_notes = Column(String, nullable=True)

    # Relationship: One patient can have many IVR check-in logs
    ivr_logs = relationship("IVRLog", back_populates="patient", cascade="all, delete-orphan")

class IVRLog(Base):
    __tablename__ = "ivr_logs"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Stores the raw speech-to-text if needed later
    transcript = Column(String, nullable=True) 
    
    # Stores the dictionary of "Friendly Questions" responses
    # Example: {"shortness_of_breath": "Yes", "leg_swelling": "No"}
    symptoms = Column(JSON) 
    
    # The calculated risk (e.g., 0.85 for 85% risk)
    risk = Column(Float) 
    
    # Stores feature importance data for explainability (if using an ML model)
    shap = Column(JSON, nullable=True) 
    
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="ivr_logs")
