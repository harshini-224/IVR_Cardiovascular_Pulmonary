from pydantic import BaseModel
from typing import Optional

class PatientCreate(BaseModel):
    name: str
    phone: str
    disease: str

class PatientOut(PatientCreate):
    id: int
    active: bool

    class Config:
        orm_mode = True
