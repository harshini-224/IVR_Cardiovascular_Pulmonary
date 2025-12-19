from sqlalchemy import Column, Integer, Text, Boolean, Date, Float
from sqlalchemy.sql import func
from database import Base

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    phone = Column(Text, unique=True)
    diagnosis = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    active = Column(Boolean, default=True)

class IVRLog(Base):
    __tablename__ = "ivr_logs"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer)
    transcript = Column(Text)
    symptoms = Column(Text)
    followups = Column(Text)
    risk = Column(Float)
    created_at = Column(Date, server_default=func.now())
