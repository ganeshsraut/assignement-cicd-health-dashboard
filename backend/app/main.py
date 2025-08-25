from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import os

from .config import settings
from .database import init_db, get_db, Session
from . import models
from .routes import router as api_router
from .ingestor import start_scheduler

app = FastAPI(
    title="CI/CD Pipeline Health Dashboard API",
    version="1.0.0",
)

# CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()
    # Start the polling scheduler
    start_scheduler()

# Mount API routes under /api
app.include_router(api_router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}
