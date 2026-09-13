from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.auth_utils import get_current_user
from jobs.models import Job,JobSkill
from skills.models import Skill 
from accounts.models import User


router = APIRouter(
    prefix="/api/jobs",
    tags=["Jobs"],
    dependencies=[Depends(get_current_user)]
)


class JobCreateRequest(BaseModel):

    recruiter_id: int
    job_title: str
    department: str | None = None
    location: str | None = None
    employment_type: str | None = None
    description: str
    experience_min: float | None = None
    experience_max: float | None = None
    status: str = "Draft"


@router.post("/")
def create_job(job: JobCreateRequest):

    recruiter = User.objects.filter(
        user_id=job.recruiter_id
    ).first()

    if not recruiter:
        return {
            "message": "Recruiter not found"
        }

    new_job = Job.objects.create(
        recruiter=recruiter,
        job_title=job.job_title,
        department=job.department,
        location=job.location,
        employment_type=job.employment_type,
        description=job.description,
        experience_min=job.experience_min,
        experience_max=job.experience_max,
        status=job.status
    )

    return {
        "message": "Job created successfully",
        "job": {
            "job_id": new_job.job_id,
            "recruiter_id": recruiter.user_id,
            "job_title": new_job.job_title,
            "department": new_job.department,
            "location": new_job.location,
            "employment_type": new_job.employment_type,
            "description": new_job.description,
            "experience_min": (
                float(new_job.experience_min)
                if new_job.experience_min is not None
                else None
            ),
            "experience_max": (
                float(new_job.experience_max)
                if new_job.experience_max is not None
                else None
            ),
            "status": new_job.status
        }
    }


# =========================
# Get All Jobs
# =========================

@router.get("/")
def get_jobs():

    jobs = Job.objects.all().order_by("-created_at")

    job_list = []

    for job in jobs:

        job_list.append({
            "job_id": job.job_id,
            "recruiter_id": job.recruiter_id,
            "job_title": job.job_title,
            "department": job.department,
            "location": job.location,
            "employment_type": job.employment_type,
            "description": job.description,
            "experience_min": (
                float(job.experience_min)
                if job.experience_min is not None
                else None
            ),
            "experience_max": (
                float(job.experience_max)
                if job.experience_max is not None
                else None
            ),
            "status": job.status,
            "created_at": job.created_at,
            "updated_at": job.updated_at
        })

    return {
        "message": "Jobs fetched successfully",
        "count": len(job_list),
        "jobs": job_list
    }


# =========================
# Get Single Job
# =========================

@router.get("/{job_id}")
def get_job(job_id: int):

    job = Job.objects.filter(
        job_id=job_id
    ).first()

    if not job:
        return {
            "message": "Job not found"
        }

    return {
        "message": "Job fetched successfully",
        "job": {
            "job_id": job.job_id,
            "recruiter_id": job.recruiter_id,
            "job_title": job.job_title,
            "department": job.department,
            "location": job.location,
            "employment_type": job.employment_type,
            "description": job.description,
            "experience_min": (
                float(job.experience_min)
                if job.experience_min is not None
                else None
            ),
            "experience_max": (
                float(job.experience_max)
                if job.experience_max is not None
                else None
            ),
            "status": job.status,
            "created_at": job.created_at,
            "updated_at": job.updated_at
        }
    }


# =========================
# Update Job
# =========================

class JobUpdateRequest(BaseModel):

    job_title: str | None = None
    department: str | None = None
    location: str | None = None
    employment_type: str | None = None
    description: str | None = None
    experience_min: float | None = None
    experience_max: float | None = None
    status: str | None = None


@router.put("/{job_id}")
def update_job(job_id: int, job_data: JobUpdateRequest):

    job = Job.objects.filter(
        job_id=job_id
    ).first()

    if not job:
        return {
            "message": "Job not found"
        }

    if job_data.job_title is not None:
        job.job_title = job_data.job_title

    if job_data.department is not None:
        job.department = job_data.department

    if job_data.location is not None:
        job.location = job_data.location

    if job_data.employment_type is not None:
        job.employment_type = job_data.employment_type

    if job_data.description is not None:
        job.description = job_data.description

    if job_data.experience_min is not None:
        job.experience_min = job_data.experience_min

    if job_data.experience_max is not None:
        job.experience_max = job_data.experience_max

    if job_data.status is not None:
        job.status = job_data.status

    job.save()

    return {
        "message": "Job updated successfully",
        "job": {
            "job_id": job.job_id,
            "recruiter_id": job.recruiter_id,
            "job_title": job.job_title,
            "department": job.department,
            "location": job.location,
            "employment_type": job.employment_type,
            "description": job.description,
            "experience_min": (
                float(job.experience_min)
                if job.experience_min is not None
                else None
            ),
            "experience_max": (
                float(job.experience_max)
                if job.experience_max is not None
                else None
            ),
            "status": job.status,
            "created_at": job.created_at,
            "updated_at": job.updated_at
        }
    }

# =========================
# Close Job
# =========================

@router.patch("/{job_id}/close")
def close_job(job_id: int):

    job = Job.objects.filter(
        job_id=job_id
    ).first()

    if not job:
        return {
            "message": "Job not found"
        }

    job.status = "Closed"
    job.save()

    return {
        "message": "Job closed successfully",
        "job": {
            "job_id": job.job_id,
            "job_title": job.job_title,
            "status": job.status,
            "updated_at": job.updated_at
        }
    }


# new
class JobSkillCreate(BaseModel):
    job_id: int
    skill_id: int
    importance: str
    min_experience: float | None = None
    weight: float | None = None


@router.post("/skills")
def add_job_skill(data: JobSkillCreate):

    # Check job
    try:
        job = Job.objects.get(job_id=data.job_id)
    except Job.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    # Check skill
    try:
        skill = Skill.objects.get(skill_id=data.skill_id)
    except Skill.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Skill not found"
        )

    # Check importance
    if data.importance not in ["Required", "Preferred"]:
        raise HTTPException(
            status_code=400,
            detail="Importance must be Required or Preferred"
        )

    # Check duplicate
    existing = JobSkill.objects.filter(
        job=job,
        skill=skill
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="This skill is already added to this job"
        )

    job_skill = JobSkill.objects.create(
        job=job,
        skill=skill,
        importance=data.importance,
        min_experience=data.min_experience,
        weight=data.weight
    )

    return {
        "message": "Job skill added successfully",
        "job_skill_id": job_skill.job_skill_id,
        "job_id": job.job_id,
        "job_title": job.job_title,
        "skill_id": skill.skill_id,
        "skill_name": skill.skill_name,
        "importance": job_skill.importance,
        "min_experience": job_skill.min_experience,
        "weight": job_skill.weight
    }


@router.get("/{job_id}/skills")
def get_job_skills(job_id: int):

    try:
        job = Job.objects.get(job_id=job_id)
    except Job.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    job_skills = JobSkill.objects.filter(
        job=job
    ).select_related("skill")

    result = []

    for job_skill in job_skills:
        result.append({
            "job_skill_id": job_skill.job_skill_id,
            "skill_id": job_skill.skill.skill_id,
            "skill_name": job_skill.skill.skill_name,
            "importance": job_skill.importance,
            "min_experience": job_skill.min_experience,
            "weight": job_skill.weight
        })

    return {
        "job_id": job.job_id,
        "job_title": job.job_title,
        "skills": result
    }
