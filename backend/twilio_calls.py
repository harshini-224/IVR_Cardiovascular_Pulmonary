import os
from twilio.rest import Client

client = Client(
    os.environ["TWILIO_SID"],
    os.environ["TWILIO_AUTH"]
)

def call_patient(phone: str):
    call = client.calls.create(
        to=phone,
        from_=os.environ["TWILIO_NUMBER"],
        url=f"{os.environ['BACKEND_URL']}/twilio/voice"
    )
    return call.sid
