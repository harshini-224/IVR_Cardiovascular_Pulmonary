import logging
from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
from models import Patient
from twilio_calls import call_patient
from datetime import datetime, timedelta

# Setup logging to see the scheduler activity in your Render logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def daily_calls():
    """
    This function runs daily. It finds all active patients 
    and triggers a Twilio call if they are in their 30-day window.
    """
    db = SessionLocal()
    try:
        # Fetch only active patients
        patients = db.query(Patient).filter(Patient.active == True).all()
        
        for p in patients:
            # Only call patients for the first 30 days after enrollment
            if (datetime.utcnow() - p.enrolled_on).days <= 30:
                logger.info(f"Triggering scheduled call for {p.name} (ID: {p.id})")
                
                # We pass BOTH the phone and the ID
                # The ID is crucial so main.py knows which disease-track to use
                try:
                    call_patient(p.phone, p.id)
                except Exception as e:
                    logger.error(f"Failed to call {p.phone}: {e}")
            else:
                # Optional: Deactivate patient after 30 days automatically
                # p.active = False
                # db.commit()
                pass
                
    finally:
        db.close()

# Schedule the task: Runs every day at 10:00 AM
scheduler.add_job(daily_calls, "cron", hour=10, minute=0)

# Start the scheduler
scheduler.start()
