import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def call_patient(phone_number: str, patient_id: int):
    """
    Triggers an outbound call via Twilio.
    Passes the patient_id to the webhook so the IVR knows who is answering.
    """
    # 1. Get credentials from environment variables
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_number = os.getenv("TWILIO_NUMBER")
    
    # This must be your public Render URL (e.g., https://my-backend.onrender.com)
    backend_url = os.getenv("BACKEND_URL")

    # 2. Initialize the Twilio Client
    client = Client(account_sid, auth_token)

    try:
        # 3. Create the call
        # The 'url' tells Twilio where to fetch the TwiML (the voice instructions)
        call = client.calls.create(
            to=phone_number,
            from_=twilio_number,
            url=f"{backend_url}/twilio/voice?patient_id={patient_id}"
        )
        
        print(f"Successfully initiated call to {phone_number}. SID: {call.sid}")
        return call.sid

    except Exception as e:
        print(f"Error triggering Twilio call: {e}")
        return None
