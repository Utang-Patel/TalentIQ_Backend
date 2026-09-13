import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from pydantic import BaseModel
from typing import Literal


load_dotenv()


class GeneratedQuestion(BaseModel):
    question: str
    type: Literal[
        "Technical",
        "Behavioral",
        "Experience",
        "Skill Gap"
    ]
    difficulty: Literal["Easy", "Medium", "Hard"]
    related_skill: str | None
    reason: str


class GeneratedQuestions(BaseModel):
    questions: list[GeneratedQuestion]


def generate_interview_questions(
    candidate_name,
    resume_text,
    job_title,
    job_description,
    candidate_skills,
    required_skills,
    skill_gaps,
    experience,
    analysis_scores
):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an expert technical recruiter.

Generate exactly 5 personalized interview questions.

Candidate:
{candidate_name}

Experience:
{experience} years

Resume:
{resume_text}

Job:
{job_title}

Job Description:
{job_description}

Candidate Skills:
{candidate_skills}

Required Skills:
{required_skills}

Skill Gaps:
{skill_gaps}

Analysis Scores:
{analysis_scores}

Question distribution:
- 2 Technical
- 1 Behavioral
- 1 Experience
- 1 Skill Gap

Rules:
- Questions must be personalized.
- Do not invent candidate experience.
- Technical questions should relate to the candidate's skills and job.
- Skill Gap question must target an actual skill gap.
- Keep questions suitable for a real interview.
- related_skill must be a provided skill or null.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GeneratedQuestions,
        ),
    )

    return GeneratedQuestions.model_validate_json(response.text)