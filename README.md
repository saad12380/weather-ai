# Weather Anomaly Predictor

## Project Summary
Weather Anomaly Predictor is a complete AI-driven weather analytics platform. It includes a FastAPI backend, machine learning models, user authentication, analytics endpoints, and a promotional website.

## Repository Structure

- `backend/` - FastAPI backend, authentication, ML integration, and API endpoints.
- `frontend/` - Dashboard assets, CSS, and JavaScript for the UI.
- `weather-ai-website/` - Static marketing website for the platform.
- `models/` - Serialized ML models and scalers used by the backend.
- `requirements.txt` - Python dependencies for the backend.

## Backend Overview

The backend lives in `backend/` and provides:
- User registration, login, password reset, and 2FA
- Weather anomaly detection and predictive analytics
- Dashboard analytics and user profile management
- API key generation and billing endpoints
- Contact form handling and newsletter subscription

## Setup Instructions

### 1. Create and activate the Python virtual environment
```powershell
cd D:\python\weather-anomaly-predictor\weather-anomaly-predictor
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. Run the backend
```powershell
cd D:\python\weather-anomaly-predictor\weather-anomaly-predictor
.\venv\Scripts\Activate.ps1
python backend\main.py
```

The application starts on `http://localhost:3000`.

## Website Development

To run the static website:
```powershell
cd D:\python\weather-anomaly-predictor\weather-anomaly-predictor\weather-ai-website
npm install
npm run dev
```

## Notes

- The root `README.md` should be inside `weather-anomaly-predictor\weather-anomaly-predictor`, not the parent folder.
- The file at `weather-ai-website/README.md` is only for the marketing website part.
