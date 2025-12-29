# 🏥 Clinical Remote Patient Monitoring (RPM) System

An intelligent, **telephony-based Remote Patient Monitoring (RPM)** platform designed to bridge the gap between patients and clinicians.  
This system automates **daily health check-ins via IVR (Interactive Voice Response)** and provides clinicians with a **transparent, data-driven risk dashboard** for early intervention.

Unlike consumer health apps, this platform prioritizes **clinical reliability, explainability, and accessibility**, requiring **no smartphone or internet access** for patients.

---

## 🌟 Phase 1: Core Features (Active)

The current version focuses on **high-reliability symptom collection** and **condition-specific clinical risk assessment**.

---

### 1. Specialized Disease Monitoring Tracks

To maintain strict medical boundaries and reduce diagnostic noise, the system operates **three independent clinical tracks**:

#### ❤️ Cardiovascular Track
Monitors for **Heart Failure** and **Acute Coronary Syndrome (ACS)** indicators:
- Chest discomfort
- Lower extremity edema
- Sudden weight gain
- Orthopnea / exertional intolerance

#### 🫁 Pulmonary Track
Monitors for **respiratory distress and airway obstruction**:
- Resting dyspnea
- Wheezing
- Changes in sputum/phlegm
- Increased inhaler usage

#### 🌡️ General Health Track
Captures **systemic deterioration indicators**:
- Fever
- Acute confusion (qSOFA-aligned)
- General functional decline

Each track operates independently to prevent cross-condition score contamination.

---

### 2. Automated Telephony (Twilio IVR)

**Accessibility-first design** ensures inclusivity for elderly and rural patients.

- 📞 **Automated voice calls** using Twilio IVR
- ❌ No smartphone, app, or internet required
- 🔢 **Binary response logic**
  - `1` → Yes
  - `2` → No
- Designed to minimize ambiguity and patient fatigue

---

### 3. Clinical Risk Engine

A deterministic, clinician-friendly scoring model built on medical standards.

- 🧠 **Expert-weighted symptom scoring**
  - Aligned with **AHA** and **WHO** guidelines
- 📊 **Dynamic normalization**
  - Raw symptom scores are normalized against a clinical constant (`2.5`)
  - Produces an intuitive **0% – 100% risk score**
- 🚫 No black-box ML models in Phase 1

---

### 4. Explainable AI Clinical Dashboard

Built for **trust, clarity, and medical accountability**.

- 🔍 **Risk Drivers**
  - Exact symptoms contributing to risk are displayed
- 📚 **Medical justification**
  - Each symptom links to authoritative protocols (e.g., *AHA ACS Guidelines*)
- 🖤 High-contrast, black-font UI optimized for clinical environments
- 🧾 Supports auditability and clinical review

---

## 🛠 Technical Stack

| Layer | Technology |
|-----|-----------|
| Backend API | FastAPI (Python 3.9+) |
| Frontend Dashboard | Streamlit |
| Database | SQLAlchemy (SQLite / PostgreSQL) |
| Telephony | Twilio Voice API + TwiML |
| Risk Analysis | Custom Clinical Weighting Logic |

---

## 🔮 Phase 2: Planned Enhancements

### 1. Predictive Trend Analysis
- 📉 **Decline velocity**
  - 7-day rolling slope of risk scores
- 🚨 **Early warning system**
  - Alerts triggered if risk increases by **>15% within 48 hours**
  - Even if absolute risk remains “Medium”

---

### 2. Natural Language Processing (NLP)

- 🎙️ **Voice-to-text transcription**
- 🧠 **Sentiment analysis**
  - Detect emotional distress
- 🚩 **Keyphrase extraction**
  - Identifies red-flag symptoms not captured by keypad input

---

### 3. Multi-Channel & Language Support

- 🌍 Multilingual IVR
  - Spanish
  - French
  - Hindi
- 💬 **SMS failover**
  - Automatically triggered if a voice call is missed

---

### 4. Wearable Integration

- ⌚ **IoT device syncing**
  - Heart rate
  - SpO₂
- 🔄 Combines **objective physiological data** with **subjective symptom reports**
- Enables a true **360° patient health view**

---

## 🚀 Installation & Setup

### 1. Environment Setup

```bash
pip install -r requirements.txt

