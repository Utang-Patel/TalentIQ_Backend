import os
from dotenv import load_dotenv
from google import genai

load_dotenv()


def calculate_semantic_score(resume_text, job_description):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=api_key)

    resume_result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=resume_text
    )

    job_result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=job_description
    )

    resume_embedding = resume_result.embeddings[0].values
    job_embedding = job_result.embeddings[0].values

    dot_product = sum(
        a * b
        for a, b in zip(resume_embedding, job_embedding)
    )

    resume_magnitude = sum(
        a * a
        for a in resume_embedding
    ) ** 0.5

    job_magnitude = sum(
        b * b
        for b in job_embedding
    ) ** 0.5

    if resume_magnitude == 0 or job_magnitude == 0:
        return 0

    cosine_similarity = (
        dot_product /
        (resume_magnitude * job_magnitude)
    )

    score = cosine_similarity * 100

    return round(max(0, min(score, 100)), 2)