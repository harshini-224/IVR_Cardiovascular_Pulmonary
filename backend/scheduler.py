from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
from models import Patient
from twilio_calls import call_patient
from datetime import datetime, timedelta

scheduler = BackgroundScheduler()

def daily_calls():
    db = SessionLocal()
    patients = db.query(Patient).filter(Patient.active == True).all()

    for p in patients:
        if (datetime.utcnow() - p.enrolled_on).days <= 30:
            call_patient(p.phone)

    db.close()

scheduler.add_job(daily_calls, "cron", hour=10)
scheduler.start()
