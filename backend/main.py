"""
Application entry point - FastAPI app, CORS, and router mounting.
Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database_models.base import Base
from database_models.database_connection import engine
from routes import admin, chat, departments, doctors, health, hospitals

# ── Create tables ────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── App ──────────────────────────────────────────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ────────────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(hospitals.router)
app.include_router(departments.router)
app.include_router(doctors.router)
app.include_router(admin.router)
app.include_router(health.router)


@app.get("/")
def home():
    return {"message": "backend Integrated"}
