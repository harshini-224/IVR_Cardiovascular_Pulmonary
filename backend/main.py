import os
from fastapi import FastAPI, Depends, Form, Query, Response, HTTPException
from sqlalchemy.orm import Session
from typing import List
import crud, models, schemas
from database import SessionLocal, engine
from twilio_calls import call_patient
from ml_engine import calculate_risk_and_shap

# Initialize database tables
models.Base.metadata.drop_all(bind=engine) 
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Patient Monitoring IVR System")

# --- SIMPLIFIED FRIENDLY QUESTIONS ---
FRIENDLY_QUESTIONS = {
    "Cardiovascular": [
        {"field": "chest_discomfort", "text": "Have you felt any new pain, pressure, or a heavy feeling in your chest today?"},
        {"field": "dizziness", "text": "Have you felt lightheaded, dizzy, or like you might faint?"},
        {"field": "shortness_of_breath", "text": "Are you finding it harder than usual to catch your breath while resting?"},
        {"field": "weight_gain", "text": "Have you noticed a sudden gain in weight, like two or more pounds since yesterday?"},
        {"field": "leg_swelling", "text": "Are your legs, ankles, or feet more swollen than they were yesterday?"},
        {"field": "palpitations", "text": "Has your heart felt like it is racing, fluttering, or skipping beats?"},
    ],
    "Pulmonary": [
        {"field": "rest_dyspnea", "text": "Is it difficult to breathe even when you are sitting still or lying down?"},
        {"field": "chest_tightness", "text": "Does your chest feel tight, as if something is squeezing your lungs?"},
        {"field": "exertional_dyspnea", "text": "Is it harder to breathe than usual when you walk or move around the house?"},
        {"field": "wheezing", "text": "Have you noticed a whistling or wheezing sound when you breathe in or out?"},
        {"field": "cough_increase", "text": "Have you been coughing more frequently or more deeply today?"},
        {"field": "phlegm_change", "text": "Have you noticed any change in the color or amount of mucus you are coughing up?"},
    ],
    "General": [
        {"field": "confusion", "text": "Have you felt unusually confused, foggy, or had trouble focusing today?"},
        {"field": "fever_chills", "text": "Have you had a fever, or have you felt very cold and shaky with chills?"},
        {"field": "condition_worsened", "text": "Overall, do you feel like your health has gotten worse since our last check-in?"},
        {"field": "nausea_vomiting", "text": "Have you felt sick to your stomach or had any vomiting today?"},
        {"field": "new_pain", "text": "Are you experiencing any new or unusual pain in other parts of your body?"},
        {"field": "fatigue", "text": "Have you felt much more tired or exhausted than usual today?"},
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
        return Response(content='<Response><Say>Hello. We could not find your records. Please contact your clinic.</Say></Response>', media_type="application/xml")
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="Polly.Amy">Hello {patient.name}. This is the automated health support team checking in on your recovery.</Say>
        <Pause length="1"/>
        <Say voice="Polly.Amy">We have a few quick questions to see how you are feeling today. It will only take a minute.</Say>
        <Say voice="Polly.Amy">During this call, please press 1 for Yes, and 2 for No.</Say>
        <Redirect method="POST">/twilio/ask?pid={patient_id}&amp;idx=0&amp;dis={patient.disease_track}</Redirect>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")

@app.post("/twilio/ask")
def ivr_ask(pid: int = Query(...), idx: int = Query(...), dis: str = Query(...)):
    survey = FRIENDLY_QUESTIONS.get(dis, [])
    
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
    
    survey = FRIENDLY_QUESTIONS.get(dis, [])
    
    if not Digits or Digits not in ["1", "2"]:
        return ivr_ask(pid, idx, dis)

    answer = "Yes" if Digits == "1" else "No"
    
    try:
        # 1. Update the database with the current answer
        log = crud.update_ivr_answer(db, pid, survey[idx]["field"], answer)

        # 2. CHECK: Is this the last question?
        if idx == len(survey) - 1:
            # IMPORTANT FIX: Use the 'log' returned directly from update_ivr_answer
            # This ensures we have the symptoms without waiting for a fresh DB query
            if log and log.symptoms:
                # We manually ensure the last answer is included in the dictionary
                current_symptoms = dict(log.symptoms)
                current_symptoms[survey[idx]["field"]] = answer 
                
                # Calculate risk using the most up-to-date symptoms
                risk_score, shap_data = calculate_risk_and_shap(dis, current_symptoms)
                crud.finalize_risk_score(db, pid, risk_score, shap_data)
            
            # 3. THE ENDING RESPONSE
            twiml = """<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say voice="Polly.Amy">Thank you so much for your time. Your updates have been shared with your clinical team.</Say>
                <Say voice="Polly.Amy">We are here for you. Have a wonderful and restful day. Goodbye.</Say>
                <Hangup/>
            </Response>"""
            return Response(content=twiml, media_type="application/xml")
        
        # If not the last question, move to next
        return ivr_ask(pid, idx + 1, dis)
        
    except Exception as e:
        print(f"Error in handle: {e}")
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error processing response.</Say><Hangup/></Response>', media_type="application/xml")
