from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from skills.models import Skill, CandidateSkill
from candidates.models import Candidate
from resumes.models import Resume

from services.auth_utils import get_current_user, require_role
from services.skill_extractor import extract_skills_from_text
from services.ai_skill_extractor import extract_skills_with_ai


router = APIRouter(
    prefix="/api/skills",
    tags=["Skills"],
    dependencies=[Depends(get_current_user)]
)


# =========================
# Skill Create - ADMIN ONLY
# =========================

class SkillCreate(BaseModel):
    skill_name: str
    category: str | None = None
    aliases: str | None = None


@router.post("/")
def create_skill(
    data: SkillCreate,
    user=Depends(require_role("admin"))
):

    existing_skill = Skill.objects.filter(
        skill_name__iexact=data.skill_name
    ).first()

    if existing_skill:
        return {
            "message": "Skill already exists",
            "skill_id": existing_skill.skill_id,
            "skill_name": existing_skill.skill_name
        }

    skill = Skill.objects.create(
        skill_name=data.skill_name,
        category=data.category,
        aliases=data.aliases
    )

    return {
        "message": "Skill created successfully",
        "skill_id": skill.skill_id,
        "skill_name": skill.skill_name,
        "category": skill.category,
        "aliases": skill.aliases
    }


# =========================
# Get All Skills
# =========================

@router.get("/")
def get_all_skills():

    skills = Skill.objects.all()

    result = []

    for skill in skills:
        result.append({
            "skill_id": skill.skill_id,
            "skill_name": skill.skill_name,
            "category": skill.category,
            "aliases": skill.aliases
        })

    return result


# =========================
# Candidate Skill Create
# =========================

class CandidateSkillCreate(BaseModel):
    candidate_id: int
    skill_id: int
    proficiency: str | None = None
    years_experience: float | None = None
    evidence_text: str | None = None
    source: str | None = None
    confidence_score: float | None = None


@router.post("/candidate")
def add_candidate_skill(data: CandidateSkillCreate):

    # 1. Check candidate
    try:
        candidate = Candidate.objects.get(
            candidate_id=data.candidate_id
        )
    except Candidate.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    # 2. Check skill
    try:
        skill = Skill.objects.get(
            skill_id=data.skill_id
        )
    except Skill.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Skill not found"
        )

    # 3. Check duplicate
    existing = CandidateSkill.objects.filter(
        candidate=candidate,
        skill=skill
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="This skill is already added to this candidate"
        )

    # 4. Create CandidateSkill
    candidate_skill = CandidateSkill.objects.create(
        candidate=candidate,
        skill=skill,
        proficiency=data.proficiency,
        years_experience=data.years_experience,
        evidence_text=data.evidence_text,
        source=data.source,
        confidence_score=data.confidence_score
    )

    return {
        "message": "Candidate skill added successfully",
        "candidate_skill_id": candidate_skill.candidate_skill_id,
        "candidate_id": candidate.candidate_id,
        "candidate_name": candidate.full_name,
        "skill_id": skill.skill_id,
        "skill_name": skill.skill_name,
        "proficiency": candidate_skill.proficiency,
        "years_experience": candidate_skill.years_experience,
        "evidence_text": candidate_skill.evidence_text,
        "source": candidate_skill.source,
        "confidence_score": candidate_skill.confidence_score
    }


# =========================
# Get Candidate Skills
# =========================

@router.get("/candidate/{candidate_id}")
def get_candidate_skills(candidate_id: int):

    # 1. Check candidate
    try:
        candidate = Candidate.objects.get(
            candidate_id=candidate_id
        )
    except Candidate.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    # 2. Get skills
    candidate_skills = CandidateSkill.objects.filter(
        candidate_id=candidate_id
    ).select_related("skill")

    result = []

    for candidate_skill in candidate_skills:
        result.append({
            "candidate_skill_id": candidate_skill.candidate_skill_id,
            "skill_id": candidate_skill.skill.skill_id,
            "skill_name": candidate_skill.skill.skill_name,
            "proficiency": candidate_skill.proficiency,
            "years_experience": candidate_skill.years_experience,
            "evidence_text": candidate_skill.evidence_text,
            "source": candidate_skill.source,
            "confidence_score": candidate_skill.confidence_score
        })

    return {
        "candidate_id": candidate.candidate_id,
        "candidate_name": candidate.full_name,
        "skills": result
    }


# =========================
# Extract Skills From Resume
# =========================

@router.post("/extract/{resume_id}")
def extract_resume_skills(resume_id: int):

    try:
        resume = Resume.objects.get(
            resume_id=resume_id
        )
    except Resume.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    if not resume.extracted_text:
        raise HTTPException(
            status_code=400,
            detail="Resume does not have extracted text"
        )

    skills = Skill.objects.all()

    matched_skills = extract_skills_from_text(
        resume.extracted_text,
        skills
    )

    saved_skills = []

    for matched_skill in matched_skills:

        skill = Skill.objects.get(
            skill_id=matched_skill["skill_id"]
        )

        existing = CandidateSkill.objects.filter(
            candidate=resume.candidate,
            skill=skill
        ).first()

        if existing:
            saved_skills.append({
                "skill_id": skill.skill_id,
                "skill_name": skill.skill_name,
                "status": "Already exists"
            })
            continue

        candidate_skill = CandidateSkill.objects.create(
            candidate=resume.candidate,
            skill=skill,
            evidence_text=f"Detected in resume: {skill.skill_name}",
            source="NLP",
            confidence_score=matched_skill["confidence_score"]
        )

        saved_skills.append({
            "candidate_skill_id": candidate_skill.candidate_skill_id,
            "skill_id": skill.skill_id,
            "skill_name": skill.skill_name,
            "status": "Added",
            "confidence_score": float(
                candidate_skill.confidence_score
            )
        })

    return {
        "message": "Resume skill extraction completed",
        "resume_id": resume.resume_id,
        "candidate_id": resume.candidate.candidate_id,
        "candidate_name": resume.candidate.full_name,
        "skills_found": saved_skills,
        "total_skills_found": len(matched_skills)
    }


# =========================
# AI Skill Extraction
# =========================

@router.post("/extract-ai/{resume_id}")
def extract_skills_with_ai_endpoint(resume_id: int):

    # Get resume
    try:
        resume = Resume.objects.get(
            resume_id=resume_id
        )
    except Resume.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    if not resume.extracted_text:
        raise HTTPException(
            status_code=400,
            detail="Resume does not have extracted text"
        )

    # Get all master skills
    master_skills = Skill.objects.all()

    master_skill_names = [
        skill.skill_name
        for skill in master_skills
    ]

    # Gemini NLP extraction
    try:
        result = extract_skills_with_ai(
            resume.extracted_text,
            master_skill_names
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI skill extraction failed: {str(e)}"
        )

    candidate = resume.candidate

    saved_skills = []

    for extracted_skill in result.skills:

        # Match AI skill with master skill
        skill = Skill.objects.filter(
            skill_name__iexact=extracted_skill.skill_name
        ).first()

        # Safety check
        if not skill:
            continue

        # Create or update candidate skill
        candidate_skill, created = CandidateSkill.objects.update_or_create(
            candidate=candidate,
            skill=skill,
            defaults={
                "proficiency": extracted_skill.proficiency,
                "years_experience": extracted_skill.years_experience,
                "evidence_text": extracted_skill.evidence_text,
                "source": "Gemini AI NLP",
                "confidence_score": extracted_skill.confidence_score
            }
        )

        saved_skills.append({
            "candidate_skill_id": candidate_skill.candidate_skill_id,
            "skill_name": skill.skill_name,
            "proficiency": candidate_skill.proficiency,
            "years_experience": (
                float(candidate_skill.years_experience)
                if candidate_skill.years_experience is not None
                else None
            ),
            "evidence_text": candidate_skill.evidence_text,
            "confidence_score": float(
                candidate_skill.confidence_score
            ),
            "source": candidate_skill.source
        })

    return {
        "message": "AI NLP skill extraction completed",
        "resume_id": resume.resume_id,
        "candidate_id": candidate.candidate_id,
        "candidate_name": candidate.full_name,
        "total_skills": len(saved_skills),
        "skills": saved_skills
    }