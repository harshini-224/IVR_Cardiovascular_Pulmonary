import os
from fastapi import FastAPI, Depends, Form, Query, Response, HTTPException
from sqlalchemy.orm import Session
from typing import List
import crud, models, schemas
from database import SessionLocal, engine
from twilio_calls import call_patient
from ml_engine import calculate_risk_and_shap

# Initialize database tables
#models.Base.metadata.drop_all(bind=engine) 
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Patient Monitoring IVR System")

# --- SIMPLIFIED FRIENDLY QUESTIONS ---
FRIENDLY_QUESTIONS = {
    "Cardiovascular": [
        {"field": "shortness_of_breath", "text": "Since you got home, has it been harder for you to breathe?"},
        {"field": "leg_swelling", "text": "Are your legs or feet puffier or more swollen than usual?"},
        {"field": "chest_discomfort", "text": "Have you felt any new pain or a heavy feeling in your chest?"},
        {"field": "weight_gain", "text": "Have you gained weight suddenly in the last few days?"},
    ],
    "Pulmonary": [
        {"field": "exertional_dyspnea", "text": "Is it harder to breathe when you walk or do simple chores?"},
        {"field": "cough_increase", "text": "Have you been coughing more often since you got home?"},
        {"field": "wheezing", "text": "Do you hear a whistling sound when you breathe?"},
        {"field": "rest_dyspnea", "text": "Is it hard to breathe even when you are just sitting still?"},
    ],
    "General": [
        {"field": "fever_chills", "text": "Have you had a fever or felt very cold and shaky?"},
        {"field": "confusion", "text": "Have you felt mixed up or had trouble remembering things?"}
    ]
}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- DASHBOARD ENDPOINTS ---

@app.post("/patients", response_model=schemas.PatientOut)
def enroll_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    # crud.create_patient now uses 'phone_number' internally
    return crud.create_patient(db, patient.dict())

@app.get("/patients", response_model=List[schemas.PatientOut])
def list_patients(db: Session = Depends(get_db)):
    return crud.get_patients(db)

@app.get("/patients/{pid}/all-logs", response_model=List[schemas.IVRLogOut])
def get_all_logs(pid: int, db: Session = Depends(get_db)):
    return crud.get_all_logs(db, pid)

# --- DOCTOR-IN-THE-LOOP VERIFICATION ---

@app.put("/logs/{log_id}/verify")
def verify_log(log_id: int, data: schemas.IVRLogUpdate, db: Session = Depends(get_db)):
    """Updates a specific IVR log with doctor status and notes."""
    updated_log = crud.update_log_status(db, log_id, data.doctor_status, data.doctor_notes)
    if not updated_log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return {"status": "verified"}

@app.put("/patients/{pid}/note")
def update_patient_general_note(pid: int, data: schemas.DoctorNoteUpdate, db: Session = Depends(get_db)):
    updated_patient = crud.update_patient_note(db, pid, data.note)
    if not updated_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"status": "success"}

@app.delete("/patients/{pid}")
def remove_patient(pid: int, db: Session = Depends(get_db)):
    success = crud.delete_patient(db, pid)
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"status": "success"}

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
        return Response(content='<Response><Say>Patient not found.</Say></Response>', media_type="application/xml")
    
    # Pass 'disease_track' instead of 'disease' to match updated models
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say>Hello {patient.name}. This is your automated health check-in.</Say>
        <Say>For Yes, press 1. For No, press 2.</Say>
        <Redirect method="POST">/twilio/ask?pid={patient_id}&amp;idx=0&amp;dis={patient.disease_track}</Redirect>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")

@app.post("/twilio/ask")
def ivr_ask(pid: int = Query(...), idx: int = Query(...), dis: str = Query(...)):
    survey = FRIENDLY_QUESTIONS.get(dis, []) + FRIENDLY_QUESTIONS.get("General", [])
    
    if idx >= len(survey):
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Thank you. Your responses have been recorded. Goodbye.</Say><Hangup/></Response>', media_type="application/xml")

    q = survey[idx]
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Gather action="/twilio/handle?pid={pid}&amp;idx={idx}&amp;dis={dis}" method="POST" numDigits="1" timeout="10">
            <Say>{q['text']}</Say>
        </Gather>
        <Redirect method="POST">/twilio/ask?pid={pid}&amp;idx={idx}&amp;dis={dis}</Redirect>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")

@app.post("/twilio/handle")
def ivr_handle(pid: int = Query(...), idx: int = Query(...), dis: str = Query(...), 
               Digits: str = Form(None), db: Session = Depends(get_db)):
    
    survey = FRIENDLY_QUESTIONS.get(dis, []) + FRIENDLY_QUESTIONS.get("General", [])
    
    if not Digits or Digits not in ["1", "2"]:
        return ivr_ask(pid, idx, dis)

    answer = "Yes" if Digits == "1" else "No"
    try:
        crud.update_ivr_answer(db, pid, survey[idx]["field"], answer)

        if idx == len(survey) - 1:
            log = crud.get_latest_log(db, pid)
            if log and log.symptoms:
                # Engine now requires 'dis' (disease_track) for clinical weighting
                risk_score, shap_data = calculate_risk_and_shap(dis, log.symptoms)
                crud.finalize_risk_score(db, pid, risk_score, shap_data)
        
        return ivr_ask(pid, idx + 1, dis)
        
    except Exception as e:
        print(f"Error in handle: {e}")
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error processing response.</Say><Hangup/></Response>', media_type="application/xml")
