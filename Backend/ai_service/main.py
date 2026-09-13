import os
import sys

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
# =========================
# Add Django project path
# =========================

DJANGO_PROJECT_PATH = r"D:\TALENT_IQ\Backend\HireSense"

sys.path.insert(0, DJANGO_PROJECT_PATH)


# =========================
# Django settings
# =========================

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "HireSense.settings"
)


# =========================
# Start Django
# =========================

import django

django.setup()



# =========================
# Import routers
# =========================

from routers.auth import router
from routers.jobs import router as jobs_router
from routers.candidates import router as candidates_router
from routers.resumes import router as resumes_router
from routers.skills import router as skills_router
from routers.analysis import router as analysis_router
# =========================
# FastAPI
# =========================

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "TalentIQ FastAPI is running"
    }


@app.get("/api")
def api_home():
    return {
        "message": "TalentIQ API is running",
        "routes": {
            "register": "POST /api/auth/register",
            "login": "POST /api/auth/login",
            "create_job": "POST /api/jobs/",
             "create_candidate": "POST /api/candidates/"
        }
    }


# =========================
# Include routers
# =========================

app.include_router(router)
app.include_router(jobs_router)
app.include_router(candidates_router)
app.include_router(resumes_router)
app.include_router(skills_router)
app.include_router(analysis_router)