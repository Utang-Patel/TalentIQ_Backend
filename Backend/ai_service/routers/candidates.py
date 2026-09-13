from fastapi import APIRouter
from pydantic import BaseModel

from candidates.models import Candidate
from fastapi import APIRouter, HTTPException, Depends

from services.auth_utils import get_current_user
router = APIRouter(
    prefix="/api/candidates",
    tags=["Candidates"],
    dependencies=[Depends(get_current_user)]
)


# =========================
# CREATE CANDIDATE
# =========================

class CandidateCreateRequest(BaseModel):

    full_name: str
    email: str
    phone: str | None = None
    location: str | None = None
    total_experience: float | None = None
    highest_education: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None


@router.post("/")
def create_candidate(candidate: CandidateCreateRequest):

    # Check if candidate already exists
    existing_candidate = Candidate.objects.filter(
        email=candidate.email
    ).first()

    if existing_candidate:
        return {
            "message": "Candidate already exists",
            "candidate": {
                "candidate_id": existing_candidate.candidate_id,
                "full_name": existing_candidate.full_name,
                "email": existing_candidate.email
            }
        }

    # Create new candidate
    new_candidate = Candidate.objects.create(
        full_name=candidate.full_name,
        email=candidate.email,
        phone=candidate.phone,
        location=candidate.location,
        total_experience=candidate.total_experience,
        highest_education=candidate.highest_education,
        linkedin_url=candidate.linkedin_url,
        github_url=candidate.github_url
    )

    return {
        "message": "Candidate created successfully",
        "candidate": {
            "candidate_id": new_candidate.candidate_id,
            "full_name": new_candidate.full_name,
            "email": new_candidate.email,
            "phone": new_candidate.phone,
            "location": new_candidate.location,
            "total_experience": (
                float(new_candidate.total_experience)
                if new_candidate.total_experience is not None
                else None
            ),
            "highest_education": new_candidate.highest_education,
            "linkedin_url": new_candidate.linkedin_url,
            "github_url": new_candidate.github_url,
            "created_at": new_candidate.created_at,
            "updated_at": new_candidate.updated_at
        }
    }


# =========================
# GET ALL CANDIDATES
# =========================

@router.get("/")
def get_candidates():

    candidates = Candidate.objects.all().order_by("-created_at")

    candidate_list = []

    for candidate in candidates:

        candidate_list.append({
            "candidate_id": candidate.candidate_id,
            "full_name": candidate.full_name,
            "email": candidate.email,
            "phone": candidate.phone,
            "location": candidate.location,
            "total_experience": (
                float(candidate.total_experience)
                if candidate.total_experience is not None
                else None
            ),
            "highest_education": candidate.highest_education,
            "linkedin_url": candidate.linkedin_url,
            "github_url": candidate.github_url,
            "created_at": candidate.created_at,
            "updated_at": candidate.updated_at
        })

    return {
        "message": "Candidates fetched successfully",
        "count": len(candidate_list),
        "candidates": candidate_list
    }


# =========================
# GET SINGLE CANDIDATE
# =========================

@router.get("/{candidate_id}")
def get_candidate(candidate_id: int):

    candidate = Candidate.objects.filter(
        candidate_id=candidate_id
    ).first()

    if not candidate:
        return {
            "message": "Candidate not found"
        }

    return {
        "message": "Candidate fetched successfully",
        "candidate": {
            "candidate_id": candidate.candidate_id,
            "full_name": candidate.full_name,
            "email": candidate.email,
            "phone": candidate.phone,
            "location": candidate.location,
            "total_experience": (
                float(candidate.total_experience)
                if candidate.total_experience is not None
                else None
            ),
            "highest_education": candidate.highest_education,
            "linkedin_url": candidate.linkedin_url,
            "github_url": candidate.github_url,
            "created_at": candidate.created_at,
            "updated_at": candidate.updated_at
        }
    }