from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
import time

from database import SessionLocal, engine
from models import Base
import crud
from schemas import PatientCreate, PatientOut
from typing import List
from twilio_calls import call_patient

app = FastAPI(title="IVR Post Discharge Monitoring")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup():
    retries = 5
    while retries:
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables ready")
            break
        except OperationalError:
            retries -= 1
            time.sleep(3)

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

@app.post("/call/{phone}")
def manual_call(phone: str):
    try:
        sid = call_patient(phone)
        return {"sid": sid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/twilio/voice")
def twilio_voice():
    twiml = """
    <Response>
        <Say voice="alice">
            Hello. This is your post discharge health monitoring call.
        </Say>
        <Pause length="1"/>
        <Say>
            Please describe any symptoms you are experiencing after the beep.
        </Say>
        <Record maxLength="30" timeout="5"/>
        <Say>Thank you. Goodbye.</Say>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")
