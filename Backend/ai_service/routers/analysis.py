from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from django.utils import timezone
from analysis.models import ResumeAnalysis, SkillGap, CandidateScore, InterviewQuestion,InterviewSession
from resumes.models import Resume
from jobs.models import Job, JobSkill
from skills.models import CandidateSkill, Candidate, Skill
from accounts.models import User
from services.interview_generator import generate_interview_questions as generate_with_gemini
from services.semantic_matcher import calculate_semantic_score as calculate_ai_semantic_score
from services.ai_skill_extractor import extract_skills_with_ai
from services.ai_summary_generator import generate_candidate_summary
from services.auth_utils import get_current_user

router = APIRouter(
    prefix="/api/analysis",
    tags=["Analysis"],
    dependencies=[Depends(get_current_user)]
)

def calculate_semantic_score(resume_text, job_description):
    return calculate_ai_semantic_score(
        resume_text,
        job_description
    )

def calculate_resume_quality_score(resume_text, candidate):

    score = 0

    # 1. Resume text exists
    if resume_text and len(resume_text.strip()) >= 200:
        score += 20

    # 2. Email available
    if candidate.email:
        score += 20

    # 3. Phone available
    if candidate.phone:
        score += 15

    # 4. Education available
    if candidate.highest_education:
        score += 15

    # 5. Experience information available
    if candidate.total_experience is not None:
        score += 15

    # 6. LinkedIn or GitHub available
    if candidate.linkedin_url or candidate.github_url:
        score += 15

    return score


def calculate_skill_match(candidate_skills, job_skills):

    candidate_skill_map = {
        cs.skill_id: cs
        for cs in candidate_skills
    }

    total_weight = 0
    matched_weight = 0

    matched_skills = []
    skill_gaps = []

    for job_skill in job_skills:

        weight = float(
            job_skill.weight or
            (2 if job_skill.importance == "Required" else 1)
        )

        total_weight += weight

        candidate_skill = candidate_skill_map.get(
            job_skill.skill_id
        )

        # Skill is completely missing
        if not candidate_skill:

            skill_gaps.append({
                "skill": job_skill.skill,
                "gap_type": "Missing",
                "candidate_level": None,
                "required_level": (
                    str(job_skill.min_experience)
                    if job_skill.min_experience is not None
                    else None
                ),
                "importance": job_skill.importance,
                "explanation": (
                    f"Candidate does not have "
                    f"{job_skill.skill.skill_name}."
                )
            })

            continue

        match_fraction = 1.0

        # Check minimum experience requirement
        if (
            job_skill.min_experience is not None
            and candidate_skill.years_experience is not None
        ):

            required = float(job_skill.min_experience)
            candidate_years = float(
                candidate_skill.years_experience
            )

            if required > 0 and candidate_years < required:

                match_fraction = candidate_years / required

                skill_gaps.append({
                    "skill": job_skill.skill,
                    "gap_type": "Partial",
                    "candidate_level": f"{candidate_years} years",
                    "required_level": f"{required} years",
                    "importance": job_skill.importance,
                    "explanation": (
                        f"Candidate has {candidate_years} years "
                        f"of experience in "
                        f"{job_skill.skill.skill_name}, "
                        f"but the job requires {required} years."
                    )
                })

        matched_weight += weight * match_fraction

        matched_skills.append(
            job_skill.skill.skill_name
        )

    if total_weight == 0:
        skill_match_score = 0
    else:
        skill_match_score = (
            matched_weight / total_weight
        ) * 100

    return (
        round(skill_match_score, 2),
        matched_skills,
        skill_gaps
    )


def update_candidate_rankings(job_id):

    scores = CandidateScore.objects.filter(
        analysis__job_id=job_id
    ).order_by("-final_score", "score_id")

    rank = 1

    for score in scores:

        score.ranking = rank

        score.save(
            update_fields=["ranking"]
        )

        rank += 1


@router.post("/")
def create_analysis(resume_id: int, job_id: int):

    # -----------------------------------
    # 1. Get Resume
    # -----------------------------------

    try:
        resume = Resume.objects.get(
            resume_id=resume_id
        )
    except Resume.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )


    # -----------------------------------
    # 2. Check extracted text
    # -----------------------------------

    if not resume.extracted_text:
        raise HTTPException(
            status_code=400,
            detail="Resume does not have extracted text"
        )


    # -----------------------------------
    # 3. Get Job
    # -----------------------------------

    try:
        job = Job.objects.get(
            job_id=job_id
        )
    except Job.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    existing_analysis = ResumeAnalysis.objects.filter(
    resume=resume,
    job=job
).first()

    if existing_analysis:
        return {
        "message": "Analysis already exists",
        "analysis_id": existing_analysis.analysis_id,
        "candidate_id": resume.candidate.candidate_id,
        "candidate_name": resume.candidate.full_name,
        "job_id": job.job_id,
        "job_title": job.job_title,
        "skill_match_score": float(
            existing_analysis.skill_match_score or 0
        ),
        "experience_score": float(
            existing_analysis.experience_score or 0
        ),
        "semantic_score": float(
            existing_analysis.semantic_score or 0
        ),
        "resume_quality_score": float(
            existing_analysis.resume_quality_score or 0
        ),
        "overall_score": float(
            existing_analysis.overall_score or 0
        ),
        "status": existing_analysis.status
    }


    # -----------------------------------
    # 4. Get Candidate
    # -----------------------------------

    candidate = resume.candidate

    # -----------------------------------
    # Calculate Resume Quality Score
    # -----------------------------------

    resume_quality_score = calculate_resume_quality_score(
        resume.extracted_text,
        candidate
    )



    
    # -----------------------------------
    # 5. Calculate Semantic Score
    # -----------------------------------
    semantic_score = calculate_semantic_score(
        resume.extracted_text,
        job.description
    )


    # -----------------------------------
    # 5. Calculate Experience Score
    # -----------------------------------

    candidate_experience = float(
        candidate.total_experience or 0
    )

    minimum_experience = float(
        job.experience_min or 0
    )

    if minimum_experience == 0:

        experience_score = 100

    elif candidate_experience >= minimum_experience:

        experience_score = 100

    else:

        experience_score = (
            candidate_experience /
            minimum_experience
        ) * 100

        experience_score = round(
            experience_score,
            2
        )


    # -----------------------------------
    # 6-9. Skills and Skill Match
    # -----------------------------------

    candidate_skills = CandidateSkill.objects.filter(
        candidate=candidate
    )

    job_skills = JobSkill.objects.filter(
        job=job
    )

    if not job_skills.exists():
        raise HTTPException(
            status_code=400,
            detail="No skills configured for this job"
        )

    skill_match_score, matched_skills, skill_gaps = calculate_skill_match(
        candidate_skills,
        job_skills
    )

    # -----------------------------------
    # Calculate Final Score
    # -----------------------------------

    final_score = (
         (skill_match_score * 0.50)
         + (experience_score * 0.20)
        + (semantic_score * 0.20)
        + (resume_quality_score * 0.10)
    )

    final_score = round(
        final_score,
        2
    )

    # -----------------------------------
    # 10. Create Resume Analysis
    # -----------------------------------

    analysis = ResumeAnalysis.objects.create(
        resume=resume,
        job=job,
        summary=(
            f"Candidate matched "
            f"{len(matched_skills)} out of "
            f"{job_skills.count()} job skills."
        ),
        skill_match_score=skill_match_score,
        experience_score=experience_score,
        semantic_score=semantic_score,
        resume_quality_score=resume_quality_score,
        overall_score=final_score,
        status="Completed",
        model_name="Gemini Embedding + Weighted Scoring v6",
        analyzed_at=timezone.now()
    )


    # -----------------------------------
    # 11. Save Skill Gaps
    # -----------------------------------

    for gap in skill_gaps:

        if gap["gap_type"] == "Missing":
            severity = (
                "High"
                if gap["importance"] == "Required"
                else "Medium"
            )
        else:
            severity = (
                "Medium"
                if gap["importance"] == "Required"
                else "Low"
            )

        SkillGap.objects.create(
            analysis=analysis,
            skill=gap["skill"],
            gap_type=gap["gap_type"],
            candidate_level=gap["candidate_level"],
            required_level=gap["required_level"],
            explanation=gap["explanation"],
            severity=severity
        )

    # -----------------------------------
    # 12. Create Candidate Score
    # -----------------------------------

    candidate_score = CandidateScore.objects.create(
        analysis=analysis,
        skill_match_score=skill_match_score,
        experience_score=experience_score,
        education_score=None,
        semantic_score=semantic_score,
        resume_quality_score=resume_quality_score,
        final_score=final_score,
        ranking=None,
        scoring_version="v6-ai-semantic-score"
    )

    update_candidate_rankings(job.job_id)
    candidate_score.refresh_from_db()
    # -----------------------------------
    # 13. Return Result
    # -----------------------------------

    return {

        "message": "Resume analysis completed",

        "analysis_id": analysis.analysis_id,

        "candidate_id": candidate.candidate_id,

        "candidate_name": candidate.full_name,

        "job_id": job.job_id,

        "job_title": job.job_title,

        "skill_match_score": skill_match_score,

        "experience_score": experience_score,

        "semantic_score": semantic_score,

        "resume_quality_score": resume_quality_score,

        "matched_skills": matched_skills,

        "missing_skills": missing_skills,

        "candidate_score": {

            "score_id": candidate_score.score_id,

            "final_score": float(
                candidate_score.final_score
            ),

            "ranking": candidate_score.ranking,

            "scoring_version": (
                candidate_score.scoring_version
            )
        },

        "status": analysis.status
    }

@router.post("/recalculate/{analysis_id}")
def recalculate_analysis(analysis_id: int):

    try:
        analysis = ResumeAnalysis.objects.get(
            analysis_id=analysis_id
        )
    except ResumeAnalysis.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )

    resume = analysis.resume
    candidate = resume.candidate
    job = analysis.job

    if not resume.extracted_text:
        raise HTTPException(
            status_code=400,
            detail="Resume does not have extracted text"
        )

    # AI Semantic Score
    semantic_score = calculate_semantic_score(
        resume.extracted_text,
        job.description
    )

    # Resume Quality
    resume_quality_score = calculate_resume_quality_score(
        resume.extracted_text,
        candidate
    )

    # Experience Score
    candidate_experience = float(
        candidate.total_experience or 0
    )

    minimum_experience = float(
        job.experience_min or 0
    )

    if minimum_experience == 0:
        experience_score = 100
    elif candidate_experience >= minimum_experience:
        experience_score = 100
    else:
        experience_score = round(
            (candidate_experience / minimum_experience) * 100,
            2
        )

    # Candidate Skills
    candidate_skills = CandidateSkill.objects.filter(
        candidate=candidate
    )

    # Job Skills
    job_skills = JobSkill.objects.filter(
        job=job
    )

    if not job_skills.exists():
        raise HTTPException(
            status_code=400,
            detail="No skills configured for this job"
        )

    skill_match_score, matched_skills, skill_gaps = calculate_skill_match(
        candidate_skills,
        job_skills
    )

    # Final Score
    final_score = round(
        (skill_match_score * 0.50)
        + (experience_score * 0.20)
        + (semantic_score * 0.20)
        + (resume_quality_score * 0.10),
        2
    )

    # Update Analysis
    analysis.skill_match_score = skill_match_score
    analysis.experience_score = experience_score
    analysis.semantic_score = semantic_score
    analysis.resume_quality_score = resume_quality_score
    analysis.overall_score = final_score
    analysis.model_name = "Gemini Embedding + Weighted Scoring v6"
    analysis.status = "Completed"
    analysis.analyzed_at = timezone.now()

    analysis.save()

    # Replace old skill gaps
    SkillGap.objects.filter(
        analysis=analysis
    ).delete()

    for gap in skill_gaps:

        if gap["gap_type"] == "Missing":
            severity = (
                "High"
                if gap["importance"] == "Required"
                else "Medium"
            )
        else:
            severity = (
                "Medium"
                if gap["importance"] == "Required"
                else "Low"
            )

        SkillGap.objects.create(
            analysis=analysis,
            skill=gap["skill"],
            gap_type=gap["gap_type"],
            candidate_level=gap["candidate_level"],
            required_level=gap["required_level"],
            explanation=gap["explanation"],
            severity=severity
        )

    # Recreate skill gaps
    SkillGap.objects.filter(analysis=analysis).delete()

    for gap in skill_gaps:
        severity = (
            "High" if gap["importance"] == "Required" and gap["gap_type"] == "Missing"
            else "Medium" if gap["importance"] == "Required"
            else "Medium" if gap["gap_type"] == "Missing"
            else "Low"
        )

        SkillGap.objects.create(
            analysis=analysis,
            skill=gap["skill"],
            gap_type=gap["gap_type"],
            candidate_level=gap["candidate_level"],
            required_level=gap["required_level"],
            explanation=gap["explanation"],
            severity=severity
        )

    # Delete old score
    CandidateScore.objects.filter(
        analysis=analysis
    ).delete()

    # Create new score
    candidate_score = CandidateScore.objects.create(
        analysis=analysis,
        skill_match_score=skill_match_score,
        experience_score=experience_score,
        education_score=None,
        semantic_score=semantic_score,
        resume_quality_score=resume_quality_score,
        final_score=final_score,
        ranking=None,
        scoring_version="v6-ai-semantic-score"
    )

    # Update ranking
    update_candidate_rankings(job.job_id)

    candidate_score.refresh_from_db()

    return {
        "message": "Analysis recalculated with AI",
        "analysis_id": analysis.analysis_id,
        "semantic_score": semantic_score,
        "skill_match_score": skill_match_score,
        "experience_score": experience_score,
        "resume_quality_score": resume_quality_score,
        "overall_score": final_score,
        "ranking": candidate_score.ranking,
        "model_name": analysis.model_name,
        "scoring_version": candidate_score.scoring_version
    }

# ============================================
# FULL AI ANALYSIS WORKFLOW
# ============================================

@router.post("/full/{resume_id}/{job_id}")
def full_ai_analysis(resume_id: int, job_id: int):

    try:
        resume = Resume.objects.get(resume_id=resume_id)
    except Resume.DoesNotExist:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.extracted_text:
        raise HTTPException(status_code=400, detail="Resume does not have extracted text")

    try:
        job = Job.objects.get(job_id=job_id)
    except Job.DoesNotExist:
        raise HTTPException(status_code=404, detail="Job not found")

    candidate = resume.candidate

    # 1. AI/NLP skill extraction
    master_skills = Skill.objects.all()
    master_skill_names = [skill.skill_name for skill in master_skills]

    try:
        ai_result = extract_skills_with_ai(
            resume.extracted_text,
            master_skill_names
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI skill extraction failed: {str(e)}")

    for item in ai_result.skills:
        skill = Skill.objects.filter(skill_name__iexact=item.skill_name).first()
        if skill:
            CandidateSkill.objects.update_or_create(
                candidate=candidate,
                skill=skill,
                defaults={
                    "proficiency": item.proficiency,
                    "years_experience": item.years_experience,
                    "evidence_text": item.evidence_text,
                    "source": "Gemini AI NLP",
                    "confidence_score": item.confidence_score
                }
            )

    # 2. Create or recalculate analysis
    existing = ResumeAnalysis.objects.filter(
        resume=resume,
        job=job
    ).first()

    if existing:
        result = recalculate_analysis(existing.analysis_id)
        analysis_id = existing.analysis_id
    else:
        result = create_analysis(resume_id, job_id)
        analysis_id = result["analysis_id"]

    analysis = ResumeAnalysis.objects.get(analysis_id=analysis_id)

    # 3. AI summary
    candidate_skills = CandidateSkill.objects.filter(candidate=candidate)
    job_skills = JobSkill.objects.filter(job=job)
    skill_gaps = SkillGap.objects.filter(analysis=analysis)

    try:
        summary = generate_candidate_summary(
            candidate_name=candidate.full_name,
            job_title=job.job_title,
            resume_text=resume.extracted_text,
            matched_skills=[s.skill.skill_name for s in candidate_skills],
            missing_skills=[g.skill.skill_name for g in skill_gaps],
            skill_match_score=float(analysis.skill_match_score or 0),
            experience_score=float(analysis.experience_score or 0),
            semantic_score=float(analysis.semantic_score or 0),
            resume_quality_score=float(analysis.resume_quality_score or 0),
            overall_score=float(analysis.overall_score or 0)
        )
        analysis.summary = summary
        analysis.save(update_fields=["summary"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI summary generation failed: {str(e)}")

    # 4. AI interview questions
    gemini_questions = InterviewQuestion.objects.filter(
        analysis=analysis,
        generated_by="Gemini AI"
    )

    if not gemini_questions.exists():
        try:
            question_result = generate_ai_interview_questions(
                analysis.analysis_id
            )
            question_list = question_result.get("questions", [])
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"AI interview question generation failed: {str(e)}"
            )
    else:
        question_list = [
            {
                "question_id": q.question_id,
                "question": q.question,
                "type": q.type,
                "difficulty": q.difficulty,
                "related_skill": q.related_skill.skill_name if q.related_skill else None,
                "reason": q.reason,
                "generated_by": q.generated_by
            }
            for q in gemini_questions
        ]

    return {
        "message": "Full AI resume analysis completed",
        "analysis_id": analysis.analysis_id,
        "candidate_id": candidate.candidate_id,
        "candidate_name": candidate.full_name,
        "job_id": job.job_id,
        "job_title": job.job_title,
        "semantic_score": float(analysis.semantic_score or 0),
        "skill_match_score": float(analysis.skill_match_score or 0),
        "experience_score": float(analysis.experience_score or 0),
        "resume_quality_score": float(analysis.resume_quality_score or 0),
        "overall_score": float(analysis.overall_score or 0),
        "summary": analysis.summary,
        "interview_questions": question_list,
        "skill_gaps": [
            {
                "skill": gap.skill.skill_name,
                "gap_type": gap.gap_type,
                "severity": gap.severity,
                "explanation": gap.explanation
            }
            for gap in skill_gaps
        ]
    }


# ============================================
# GEMINI AI INTERVIEW QUESTIONS
# ============================================

@router.post("/questions/generate/{analysis_id}")
def generate_ai_interview_questions(analysis_id: int):

    # 1. Get Analysis
    try:
        analysis = ResumeAnalysis.objects.get(
            analysis_id=analysis_id
        )
    except ResumeAnalysis.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )

    # 2. Get Resume and Candidate
    resume = analysis.resume
    candidate = resume.candidate
    job = analysis.job

    if not resume.extracted_text:
        raise HTTPException(
            status_code=400,
            detail="Resume does not have extracted text"
        )

    # 3. Candidate Skills
    candidate_skills = CandidateSkill.objects.filter(
        candidate=candidate
    )

    candidate_skill_names = [
        skill.skill.skill_name
        for skill in candidate_skills
    ]

    # 4. Job Skills
    job_skills = JobSkill.objects.filter(
        job=job
    )

    required_skill_names = [
        skill.skill.skill_name
        for skill in job_skills
    ]

    # 5. Skill Gaps
    skill_gaps = SkillGap.objects.filter(
        analysis=analysis
    )

    skill_gap_data = []

    for gap in skill_gaps:
        skill_gap_data.append({
            "skill": gap.skill.skill_name,
            "type": gap.gap_type,
            "severity": gap.severity,
            "explanation": gap.explanation
        })

    # 6. Analysis Scores
    analysis_scores = {
        "skill_match_score": float(
            analysis.skill_match_score or 0
        ),
        "experience_score": float(
            analysis.experience_score or 0
        ),
        "semantic_score": float(
            analysis.semantic_score or 0
        ),
        "resume_quality_score": float(
            analysis.resume_quality_score or 0
        ),
        "overall_score": float(
            analysis.overall_score or 0
        )
    }

    # 7. Call Gemini
    try:

        result = generate_with_gemini(
            candidate_name=candidate.full_name,
            resume_text=resume.extracted_text,
            job_title=job.job_title,
            job_description=job.description,
            candidate_skills=candidate_skill_names,
            required_skills=required_skill_names,
            skill_gaps=skill_gap_data,
            experience=float(
                candidate.total_experience or 0
            ),
            analysis_scores=analysis_scores
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Gemini generation failed: {str(e)}"
        )

    # 8. Save Gemini Questions
    saved_questions = []

    for generated_question in result.questions:

        related_skill = None

        if generated_question.related_skill:

            for skill in candidate_skills:

                if (
                    skill.skill.skill_name.lower()
                    == generated_question.related_skill.lower()
                ):
                    related_skill = skill.skill
                    break

            if not related_skill:

                for skill in job_skills:

                    if (
                        skill.skill.skill_name.lower()
                        == generated_question.related_skill.lower()
                    ):
                        related_skill = skill.skill
                        break

        question = InterviewQuestion.objects.create(
            analysis=analysis,
            question=generated_question.question,
            type=generated_question.type,
            difficulty=generated_question.difficulty,
            related_skill=related_skill,
            reason=generated_question.reason,
            generated_by="Gemini AI"
        )

        saved_questions.append({
            "question_id": question.question_id,
            "question": question.question,
            "type": question.type,
            "difficulty": question.difficulty,
            "related_skill": (
                related_skill.skill_name
                if related_skill
                else None
            ),
            "reason": question.reason,
            "generated_by": question.generated_by
        })

    # 9. Return Result
    return {
        "message": "AI interview questions generated successfully",
        "analysis_id": analysis.analysis_id,
        "total_questions": len(saved_questions),
        "generated_by": "Gemini AI",
        "questions": saved_questions
    }



# -----------------------------------
# Interview Sessions
# -----------------------------------

@router.post("/interviews/")
def create_interview_session(
    candidate_id: int,
    job_id: int,
    recruiter_id: int,
    scheduled_at: str = None,
    notes: str = None
):

    # -----------------------------------
    # 1. Get Candidate
    # -----------------------------------

    try:
        candidate = Candidate.objects.get(
            candidate_id=candidate_id
        )
    except Candidate.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    # -----------------------------------
    # 2. Get Job
    # -----------------------------------

    try:
        job = Job.objects.get(
            job_id=job_id
        )
    except Job.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    # -----------------------------------
    # 3. Get Recruiter
    # -----------------------------------

    try:
        recruiter = User.objects.get(
            user_id=recruiter_id
        )
    except User.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Recruiter not found"
        )

    # -----------------------------------
    # 4. Create Interview Session
    # -----------------------------------

    interview = InterviewSession.objects.create(
        candidate=candidate,
        job=job,
        recruiter=recruiter,
        scheduled_at=scheduled_at,
        notes=notes,
        status="Scheduled"
    )

    return {
        "message": "Interview session created successfully",
        "session_id": interview.session_id,
        "candidate_id": candidate.candidate_id,
        "candidate_name": candidate.full_name,
        "job_id": job.job_id,
        "job_title": job.job_title,
        "recruiter_id": recruiter.user_id,
        "status": interview.status,
        "scheduled_at": interview.scheduled_at,
        "notes": interview.notes
    }


# -----------------------------------
# Get All Interview Sessions
# -----------------------------------

@router.get("/interviews/")
def get_interview_sessions():

    interviews = InterviewSession.objects.all().order_by(
        "-session_id"
    )

    return {
        "total_sessions": interviews.count(),
        "interviews": [
            {
                "session_id": interview.session_id,
                "candidate_id": interview.candidate.candidate_id,
                "candidate_name": interview.candidate.full_name,
                "job_id": interview.job.job_id,
                "job_title": interview.job.job_title,
                "recruiter_id": interview.recruiter.user_id,
                "status": interview.status,
                "scheduled_at": interview.scheduled_at,
                "started_at": interview.started_at,
                "ended_at": interview.ended_at,
                "notes": interview.notes
            }
            for interview in interviews
        ]
    }


# -----------------------------------
# Get Single Interview Session
# -----------------------------------

@router.get("/interviews/{session_id}")
def get_interview_session(session_id: int):

    try:
        interview = InterviewSession.objects.get(
            session_id=session_id
        )
    except InterviewSession.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found"
        )

    return {
        "session_id": interview.session_id,
        "candidate_id": interview.candidate.candidate_id,
        "candidate_name": interview.candidate.full_name,
        "job_id": interview.job.job_id,
        "job_title": interview.job.job_title,
        "recruiter_id": interview.recruiter.user_id,
        "status": interview.status,
        "scheduled_at": interview.scheduled_at,
        "started_at": interview.started_at,
        "ended_at": interview.ended_at,
        "notes": interview.notes
    }


# -----------------------------------
# Update Interview Status
# -----------------------------------

@router.patch("/interviews/{session_id}/status")
def update_interview_status(
    session_id: int,
    status: str
):

    try:
        interview = InterviewSession.objects.get(
            session_id=session_id
        )
    except InterviewSession.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found"
        )

    allowed_statuses = [
        "Scheduled",
        "In Progress",
        "Completed",
        "Cancelled"
    ]

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid interview status"
        )

    interview.status = status

    if status == "In Progress":
        from django.utils import timezone
        interview.started_at = timezone.now()

    elif status == "Completed":
        from django.utils import timezone
        interview.ended_at = timezone.now()

    interview.save()

    return {
        "message": "Interview status updated successfully",
        "session_id": interview.session_id,
        "status": interview.status,
        "started_at": interview.started_at,
        "ended_at": interview.ended_at
    }



# ============================================
# INTERVIEW QUESTIONS
# ============================================

class InterviewQuestionCreate(BaseModel):
    analysis_id: int
    question: str
    type: str
    difficulty: str | None = None
    related_skill_id: int | None = None
    reason: str | None = None
    generated_by: str | None = "Rule-Based Generator v1"


@router.post("/questions/")
def create_interview_question(data: InterviewQuestionCreate):

    # Find analysis
    try:
        analysis = ResumeAnalysis.objects.get(
            analysis_id=data.analysis_id
        )
    except ResumeAnalysis.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )

    # Create question
    question = InterviewQuestion.objects.create(
        analysis=analysis,
        question=data.question,
        type=data.type,
        difficulty=data.difficulty,
        related_skill_id=data.related_skill_id,
        reason=data.reason,
        generated_by=data.generated_by
    )

    return {
        "message": "Interview question created successfully",
        "question_id": question.question_id,
        "analysis_id": analysis.analysis_id,
        "question": question.question,
        "type": question.type,
        "difficulty": question.difficulty,
        "related_skill_id": question.related_skill_id,
        "reason": question.reason,
        "generated_by": question.generated_by
    }


# ============================================
# GET QUESTIONS FOR ANALYSIS
# ============================================

@router.get("/questions/analysis/{analysis_id}")
def get_analysis_questions(analysis_id: int):

    try:
        analysis = ResumeAnalysis.objects.get(
            analysis_id=analysis_id
        )
    except ResumeAnalysis.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )

    questions = InterviewQuestion.objects.filter(
        analysis=analysis
    )

    result = []

    for question in questions:

        result.append({
            "question_id": question.question_id,
            "analysis_id": question.analysis_id,
            "question": question.question,
            "type": question.type,
            "difficulty": question.difficulty,
            "related_skill_id": question.related_skill_id,
            "reason": question.reason,
            "generated_by": question.generated_by
        })

    return {
        "analysis_id": analysis_id,
        "total_questions": len(result),
        "questions": result
    }


# ============================================
# GET SINGLE QUESTION
# ============================================

@router.get("/questions/{question_id}")
def get_interview_question(question_id: int):

    try:
        question = InterviewQuestion.objects.get(
            question_id=question_id
        )
    except InterviewQuestion.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Interview question not found"
        )

    return {
        "question_id": question.question_id,
        "analysis_id": question.analysis_id,
        "question": question.question,
        "type": question.type,
        "difficulty": question.difficulty,
        "related_skill_id": question.related_skill_id,
        "reason": question.reason,
        "generated_by": question.generated_by
    }


@router.patch("/interviews/{session_id}")
def update_interview_session(
    session_id: int,
    scheduled_at: str = None,
    notes: str = None
):

    try:
        interview = InterviewSession.objects.get(
            session_id=session_id
        )
    except InterviewSession.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found"
        )

    if scheduled_at is not None:
        interview.scheduled_at = scheduled_at

    if notes is not None:
        interview.notes = notes

    interview.save()

    return {
        "message": "Interview session updated successfully",
        "session_id": interview.session_id,
        "candidate_id": interview.candidate_id,
        "candidate_name": interview.candidate.full_name,
        "job_id": interview.job_id,
        "job_title": interview.job.job_title,
        "recruiter_id": interview.recruiter_id,
        "status": interview.status,
        "scheduled_at": interview.scheduled_at,
        "notes": interview.notes
    }