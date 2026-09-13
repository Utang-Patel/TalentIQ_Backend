import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()


class ExtractedSkill(BaseModel):
    skill_name: str
    proficiency: str | None = None
    years_experience: float | None = None
    evidence_text: str
    confidence_score: float


class ExtractedSkills(BaseModel):
    skills: list[ExtractedSkill]


def extract_skills_with_ai(resume_text, master_skills):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=api_key)

    skill_list = ", ".join(master_skills)

    prompt = f"""
You are an NLP resume skill extraction system.

Analyze this resume and extract skills ONLY from the provided master skill list.

MASTER SKILLS:
{skill_list}

RULES:
1. Do not invent skills.
2. Use the exact skill_name from the master list.
3. Identify evidence from the resume.
4. Estimate proficiency only when evidence supports it.
5. Estimate years of experience only when the resume provides enough evidence.
6. confidence_score must be between 0 and 100.
7. Return only skills actually supported by the resume.

RESUME:
{resume_text[:15000]}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractedSkills,
        ),
    )

    return ExtractedSkills.model_validate_json(response.text)