from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base
import crud
from twilio_calls import call_patient
from scheduler import scheduler

Base.metadata.create_all(bind=engine)

app = FastAPI(title="IVR Post Discharge Monitoring")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/patients")
def enroll_patient(data: dict, db: Session = Depends(get_db)):
    return crud.create_patient(db, data)

@app.get("/patients")
def list_patients(db: Session = Depends(get_db)):
    return crud.get_patients(db)

@app.delete("/patients/{pid}")
def remove_patient(pid: int, db: Session = Depends(get_db)):
    crud.delete_patient(db, pid)
    return {"status": "deleted"}

@app.post("/call/{phone}")
def manual_call(phone: str):
    sid = call_patient(phone)
    return {"sid": sid}
