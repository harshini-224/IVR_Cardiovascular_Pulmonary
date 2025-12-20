import os
import requests

COLAB_API = os.environ["COLAB_API_URL"]

def analyze_audio(audio_url: str):
    r = requests.post(
        f"{COLAB_API}/analyze",
        json={"audio_url": audio_url},
        timeout=60
    )
    r.raise_for_status()
    return r.json()
