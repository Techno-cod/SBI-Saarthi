"""
SBI Saarthi — FastAPI backend

Exposes the agent orchestrator as a small HTTP API:
  GET  /personas              -> list of all customers (id + name + tag info)
  GET  /saarthi/{customer_id} -> runs the full agent pipeline for one customer

Run with:
  uvicorn main:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents.aa_ingestion import load_personas
from agents.orchestrator import run_saarthi

app = FastAPI(title="SBI Saarthi API")

# Allow the React dev server (usually localhost:5173 or :3000) to call this API.
# For a hackathon prototype, allowing all origins is fine — tighten this if
# you ever deploy it somewhere real.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "SBI Saarthi backend is running"}


@app.get("/personas")
def get_personas():
    """Returns a lightweight list of all personas for the frontend's selector."""
    personas = load_personas()
    return [
        {
            "customer_id": p["customer_id"],
            "name": p["name"],
            "location": p["location"],
            "wellness_score": p["wellness_score"],
            "wellness_score_prev": p["wellness_score_prev"],
            "digital_activity_score": p["digital_activity_score"],
            "language_pref": p["language_pref"],
        }
        for p in personas
    ]


@app.get("/saarthi/{customer_id}")
def get_saarthi_decision(customer_id: str):
    """Runs the full agent pipeline for one customer and returns the result."""
    try:
        result = run_saarthi(customer_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))