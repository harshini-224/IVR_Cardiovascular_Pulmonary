from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

# --- PATIENT SCHEMAS ---

class PatientBase(BaseModel):
    name: str
    phone: str
    disease: str

class PatientCreate(PatientBase):
    pass

class PatientOut(PatientBase):
    id: int
    enrolled_on: datetime
    active: bool
    doctor_override: bool
    override_notes: Optional[str] = None

    class Config:
        from_attributes = True

# --- IVR LOG SCHEMAS ---

class IVRLogBase(BaseModel):
    patient_id: int
    # Dict[str, str] handles the "Yes/No" answers stored in JSON
    symptoms: Optional[Dict[str, str]] = None 
    risk: Optional[float] = 0.0
    transcript: Optional[str] = None
    shap: Optional[Dict[str, Any]] = None

class IVRLogCreate(IVRLogBase):
    pass

class IVRLogOut(IVRLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- DOCTOR ACTION SCHEMAS ---

class DoctorNoteUpdate(BaseModel):
    note: str
