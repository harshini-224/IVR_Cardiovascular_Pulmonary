from pydantic import BaseModel
from datetime import datetime

class PatientCreate(BaseModel):
    name: str
    phone: str
    disease: str

class PatientOut(PatientCreate):
    id: int
    enrolled_on: datetime
    active: bool

    class Config:
        from_attributes = True
