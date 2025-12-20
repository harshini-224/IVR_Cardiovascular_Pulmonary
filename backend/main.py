from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
import time

from database import SessionLocal, engine
from models import Base
import crud
from schemas import PatientCreate, PatientOut
from typing import List

app = FastAPI(title="IVR Post Discharge Monitoring")

# ---- DB session dependency ----
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---- CREATE TABLES USING INTERNAL DB ----
@app.on_event("startup")
def startup():
    retries = 5
    while retries:
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created")
            break
        except OperationalError:
            retries -= 1
            print("⏳ Waiting for database...")
            time.sleep(3)

# ---- ROUTES ----
@app.post("/patients", response_model=PatientOut)
def enroll_patient(data: PatientCreate, db: Session = Depends(get_db)):
    return crud.create_patient(db, data.dict())

@app.get("/patients", response_model=List[PatientOut])
def list_patients(db: Session = Depends(get_db)):
    return crud.get_patients(db)

@app.delete("/patients/{pid}")
def remove_patient(pid: int, db: Session = Depends(get_db)):
    crud.delete_patient(db, pid)
    return {"status": "deleted"}
