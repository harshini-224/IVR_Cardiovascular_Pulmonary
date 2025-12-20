# IVR Enabled Post Discharge Monitoring System

## Architecture
- Frontend: Streamlit (Render)
- Backend: FastAPI + PostgreSQL (Render)
- ML: Whisper + Clinical NER + SHAP (Colab + ngrok)
- IVR: Twilio Outgoing Calls

## Environment Variables (Render Backend)
- DATABASE_URL
- TWILIO_SID
- TWILIO_AUTH
- TWILIO_NUMBER
- BACKEND_URL
- COLAB_API_URL

## How Calls Work
1. Frontend triggers call
2. Backend uses Twilio
3. Twilio records audio
4. Audio sent to Colab ML
5. Risk + SHAP saved to DB

## ML (Colab)
Run notebook manually.
Update COLAB_API_URL in Render.

Colab is NOT stored in GitHub.
