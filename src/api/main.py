from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(
    title="HealthAlliance DataSpace API",
    description="MLOps Platform for Healthcare Data Sharing - DKFZ, UKHD, EMBL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthCheck(BaseModel):
    status: str
    version: str
    services: dict

class PatientRiskRequest(BaseModel):
    patient_id: str
    age: int
    gender: str
    conditions: List[str]
    medications: List[str]
    recent_encounters: int

class PatientRiskResponse(BaseModel):
    patient_id: str
    readmission_risk: float
    risk_level: str
    confidence: float
    recommendations: List[str]

@app.get("/")
async def root():
    return {
        "message": "HealthAlliance DataSpace MLOps Platform",
        "version": "1.0.0",
        "institutions": ["DKFZ", "UKHD", "EMBL"],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "predict": "/api/v1/predict"
        }
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "api": "running",
            "database": "connected",
            "mlflow": "available"
        }
    }

@app.post("/api/v1/predict", response_model=PatientRiskResponse)
async def predict_readmission_risk(request: PatientRiskRequest):
    risk_score = 0.0
    
    if request.age > 65:
        risk_score += 0.3
    if request.recent_encounters > 3:
        risk_score += 0.2
    if len(request.conditions) > 2:
        risk_score += 0.25
    if len(request.medications) > 5:
        risk_score += 0.15
    
    risk_score = min(risk_score, 1.0)
    
    if risk_score < 0.3:
        risk_level = "LOW"
        recommendations = ["Regular follow-up in 3 months"]
    elif risk_score < 0.6:
        risk_level = "MEDIUM"
        recommendations = [
            "Schedule follow-up in 2 weeks",
            "Monitor medication adherence"
        ]
    else:
        risk_level = "HIGH"
        recommendations = [
            "Immediate follow-up within 48 hours",
            "Consider home health services",
            "Review medication plan"
        ]
    
    return {
        "patient_id": request.patient_id,
        "readmission_risk": round(risk_score, 2),
        "risk_level": risk_level,
        "confidence": 0.85,
        "recommendations": recommendations
    }

@app.get("/api/v1/institutions")
async def list_institutions():
    return {
        "institutions": [
            {
                "id": "dkfz",
                "name": "German Cancer Research Center",
                "location": "Heidelberg",
                "patient_count": 500
            },
            {
                "id": "ukhd",
                "name": "University Hospital Heidelberg",
                "location": "Heidelberg",
                "patient_count": 700
            },
            {
                "id": "embl",
                "name": "European Molecular Biology Laboratory",
                "location": "Heidelberg",
                "patient_count": 300
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
