import os
from fastapi import FastAPI, Depends, Form, Query, Response, HTTPException
from sqlalchemy.orm import Session
from typing import List
import crud, models, schemas
from database import SessionLocal, engine
from twilio_calls import call_patient

# Initialize database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Patient Monitoring IVR System")

# --- SIMPLIFIED FRIENDLY QUESTIONS ---
FRIENDLY_QUESTIONS = {
    "Cardiovascular": [
        {"field": "shortness_of_breath", "text": "Since you got home, has it been harder for you to breathe?"},
        {"field": "leg_swelling", "text": "Are your legs or feet puffier or more swollen than usual?"},
        {"field": "chest_discomfort", "text": "Have you felt any new pain or a heavy feeling in your chest?"},
        {"field": "fatigue", "text": "Are you feeling much more tired than normal when you move around?"},
        {"field": "weight_gain", "text": "Have you gained weight suddenly in the last few days?"},
        {"field": "palpitations", "text": "Has your heart felt like it is thumping or skipping beats?"},
        {"field": "dizziness", "text": "Have you felt dizzy or like you might pass out?"}
    ],
    "Pulmonary": [
        {"field": "exertional_dyspnea", "text": "Is it harder to breathe when you walk or do simple chores?"},
        {"field": "cough_increase", "text": "Have you been coughing more often since you got home?"},
        {"field": "wheezing", "text": "Do you hear a whistling sound when you breathe?"},
        {"field": "rest_dyspnea", "text": "Is it hard to breathe even when you are just sitting still?"},
        {"field": "chest_tightness", "text": "Has your chest been feeling very tight or uncomfortable?"},
        {"field": "phlegm_change", "text": "Are you coughing up more gunk, or has the color of it changed?"}
    ],
    "General": [
        {"field": "condition_worsened", "text": "Overall, do you feel like your health is getting worse?"},
        {"field": "new_pain", "text": "Have you had any new pain that is bothering you?"},
        {"field": "fever_chills", "text": "Have you had a fever or felt very cold and shaky?"},
        {"field": "nausea_vomiting", "text": "Has your stomach been upset, or have you been throwing up?"},
        {"field": "confusion", "text": "Have you felt mixed up or had trouble remembering things?"}
    ]
}

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- DASHBOARD & PATIENT ENDPOINTS ---

# Temporary: Add this to main.py
models.Base.metadata.drop_all(bind=engine) # This deletes old tables
models.Base.metadata.create_all(bind=engine) # This creates new ones


@app.post("/patients", response_model=schemas.PatientOut)
def enroll_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    return crud.create_patient(db, patient.dict())

@app.get("/patients", response_model=List[schemas.PatientOut])
def list_patients(db: Session = Depends(get_db)):
    return crud.get_patients(db)

@app.get("/patients/{pid}/all-logs", response_model=List[schemas.IVRLogOut])
def get_all_logs(pid: int, db: Session = Depends(get_db)):
    """Fetches full 30-day history for the dashboard."""
    logs = crud.get_all_logs(db, pid)
    if not logs:
        return []
    return logs

@app.put("/patients/{pid}/note")
def update_note(pid: int, data: schemas.DoctorNoteUpdate, db: Session = Depends(get_db)):
    """API endpoint to save doctor's notes (Assessment)."""
    updated_patient = crud.update_patient_note(db, pid, data.note)
    if not updated_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"status": "success", "message": "Assessment updated"}

@app.delete("/patients/{pid}")
def remove_patient(pid: int, db: Session = Depends(get_db)):
    """API endpoint to delete a patient and their logs."""
    success = crud.delete_patient(db, pid)
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"status": "success", "message": "Patient deleted"}

@app.post("/call/{phone}")
def manual_call(phone: str, patient_id: int, db: Session = Depends(get_db)):
    crud.create_initial_log(db, patient_id)
    sid = call_patient(phone, patient_id)
    return {"status": "Called", "sid": sid}

# --- TWILIO IVR STATE MACHINE ---

@app.post("/twilio/voice")
def ivr_start(patient_id: int = Query(...), db: Session = Depends(get_db)):
    patient = crud.get_patient_by_id(db, patient_id)
    if not patient:
        return Response(content='<Response><Say voice="alice">Error: Patient not found.</Say></Response>', media_type="application/xml")
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice">Hello {patient.name}. This is a health check-in from your doctor.</Say>
        <Say voice="alice">Please listen. If your answer is Yes, press 1. If No, press 2.</Say>
        <Redirect method="POST">/twilio/ask?pid={patient_id}&amp;idx=0&amp;dis={patient.disease}</Redirect>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")

@app.post("/twilio/ask")
def ivr_ask(pid: int = Query(...), idx: int = Query(...), dis: str = Query(...)):
    survey = FRIENDLY_QUESTIONS.get(dis, []) + FRIENDLY_QUESTIONS.get("General", [])
    
    if idx >= len(survey):
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="alice">Thank you for completing your health check-in. Goodbye.</Say><Hangup/></Response>', media_type="application/xml")

    q = survey[idx]
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Gather action="/twilio/handle?pid={pid}&amp;idx={idx}&amp;dis={dis}" method="POST" numDigits="1" timeout="10">
            <Say voice="alice">{q['text']} Press 1 for Yes, 2 for No.</Say>
        </Gather>
        <Redirect method="POST">/twilio/ask?pid={pid}&amp;idx={idx}&amp;dis={dis}</Redirect>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")

@app.post("/twilio/handle")
def ivr_handle(pid: int = Query(...), idx: int = Query(...), dis: str = Query(...), Digits: str = Form(None), db: Session = Depends(get_db)):
    survey = FRIENDLY_QUESTIONS.get(dis, []) + FRIENDLY_QUESTIONS.get("General", [])
    
    if not Digits or Digits not in ["1", "2"]:
        return ivr_ask(pid, idx, dis)

    answer = "Yes" if Digits == "1" else "No"
    crud.update_ivr_answer(db, pid, survey[idx]["field"], answer)

    # Calculate risk if this is the final question
    if idx == len(survey) - 1:
        log = crud.get_latest_log(db, pid)
        if log and log.symptoms:
            yes_count = sum(1 for v in log.symptoms.values() if v == "Yes")
            # Clear 0-100 score logic
            risk_score = (yes_count / len(survey)) * 100
            crud.finalize_risk_score(db, pid, risk_score)

    return ivr_ask(pid, idx + 1, dis)
