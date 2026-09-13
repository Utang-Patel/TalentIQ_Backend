import os
from dotenv import load_dotenv
from google import genai

load_dotenv()


def generate_candidate_summary(
    candidate_name,
    job_title,
    resume_text,
    matched_skills,
    missing_skills,
    skill_match_score,
    experience_score,
    semantic_score,
    resume_quality_score,
    overall_score
):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an AI recruitment assistant.

Create a concise professional candidate evaluation summary.

Candidate: {candidate_name}
Job: {job_title}

Matched Skills:
{matched_skills}

Missing Skills:
{missing_skills}

Scores:
Skill Match: {skill_match_score}
Experience: {experience_score}
Semantic Match: {semantic_score}
Resume Quality: {resume_quality_score}
Overall Score: {overall_score}

Resume:
{resume_text[:10000]}

Requirements:
1. Write 3-5 sentences.
2. Mention strongest relevant skills.
3. Mention important skill gaps if present.
4. Mention overall suitability.
5. Do not invent experience or skills.
6. Keep the summary professional and recruiter-friendly.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return response.text.strip()