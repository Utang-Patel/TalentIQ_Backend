import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# ============================================================
# Django Project Setup
# ============================================================

DJANGO_PROJECT_PATH = r"D:\TALENT_IQ\Backend\HireSense"

sys.path.insert(0, DJANGO_PROJECT_PATH)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "HireSense.settings"
)

import django

django.setup()


# ============================================================
# Import FastAPI Routers
# ============================================================

from routers.auth import router as auth_router
from routers.jobs import router as jobs_router
from routers.candidates import router as candidates_router
from routers.resumes import router as resumes_router
from routers.skills import router as skills_router
from routers.analysis import router as analysis_router


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="TalentIQ API",
    description="AI-powered recruitment backend API",
    version="1.0.0"
)


# ============================================================
# CORS Configuration
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# Register All Routers
# ============================================================

app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(candidates_router)
app.include_router(resumes_router)
app.include_router(skills_router)
app.include_router(analysis_router)


# ============================================================
# Root Endpoint
# ============================================================

@app.get("/")
def home():
    return {
        "message": "TalentIQ FastAPI is running"
    }


# ============================================================
# Complete API List
# ============================================================

@app.get("/api")
def api_home():

    openapi_data = app.openapi()

    routes = []

    for path, path_data in openapi_data.get("paths", {}).items():

        if not path.startswith("/api"):
            continue

        for method in path_data.keys():

            method = method.upper()

            if method not in [
                "GET",
                "POST",
                "PUT",
                "PATCH",
                "DELETE"
            ]:
                continue

            routes.append({
                "method": method,
                "url": path
            })

    routes.sort(
        key=lambda x: (x["url"], x["method"])
    )

    return {
        "message": "TalentIQ API is running",
        "total_apis": len(routes),
        "routes": routes
    }
