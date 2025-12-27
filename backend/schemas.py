from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List

# --- IVR LOG SCHEMAS ---

class IVRLogBase(BaseModel):
    patient_id: int
    # Dict[str, str] handles the "Yes/No" answers stored in JSON
    symptoms: Optional[Dict[str, str]] = {} 
    shap: Optional[Dict[str, float]] = {}
    risk_score: Optional[float] = 0.0
    
    # Doctor's Assessment Fields
    doctor_status: str = "Pending"
    doctor_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    
class IVRLogCreate(IVRLogBase):
    pass

class IVRLogResponse(IVRLogBase):
    id: int
    created_at: datetime

class IVRLogUpdate(BaseModel):
    """Schema for updating the doctor's assessment only."""
    doctor_status: str
    doctor_notes: str

class IVRLogOut(IVRLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True # Allows Pydantic to read SQLAlchemy models

# --- PATIENT SCHEMAS ---

class PatientBase(BaseModel):
    name: str
    phone_number: str
    disease_track: str

class PatientCreate(PatientBase):
    pass

class PatientOut(PatientBase):
    id: int
    enrolled_on: datetime
    active: bool
    doctor_override: bool
    override_notes: Optional[str] = None
    # Included to allow the dashboard to see all check-ins for Day 1, Day 2, etc.
    logs: List[IVRLogOut] = [] 

    class Config:
        from_attributes = True

# --- DOCTOR ACTION SCHEMAS ---

class DoctorNoteUpdate(BaseModel):
    note: str
