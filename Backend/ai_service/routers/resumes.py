import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form
from fastapi import APIRouter, HTTPException, Depends
from django.conf import settings
from fastapi import Depends
from services.auth_utils import get_current_user
from pypdf import PdfReader
from docx import Document

from candidates.models import Candidate
from resumes.models import Resume


router = APIRouter(
    prefix="/api/resumes",
    tags=["Resumes"],
    dependencies=[Depends(get_current_user)]
)


# =========================
# EXTRACT PDF TEXT
# =========================

def extract_pdf_text(file_path):

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text.strip()


# =========================
# EXTRACT DOCX TEXT
# =========================

def extract_docx_text(file_path):

    document = Document(file_path)

    text = ""

    for paragraph in document.paragraphs:

        if paragraph.text.strip():
            text += paragraph.text + "\n"

    return text.strip()


# =========================
# UPLOAD RESUME
# =========================

@router.post("/upload")
def upload_resume(
    candidate_id: int = Form(...),
    file: UploadFile = File(...)
):

    # =========================
    # Check candidate
    # =========================

    candidate = Candidate.objects.filter(
        candidate_id=candidate_id
    ).first()

    if not candidate:
        return {
            "message": "Candidate not found"
        }


    # =========================
    # Check file type
    # =========================

    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]

    if file.content_type not in allowed_types:
        return {
            "message": "Only PDF and DOCX files are allowed"
        }


    # =========================
    # Read uploaded file
    # =========================

    file_content = file.file.read()

    file_size = len(file_content)


    # =========================
    # Create resume folder
    # =========================

    resume_folder = os.path.join(
        settings.MEDIA_ROOT,
        "resumes"
    )

    os.makedirs(
        resume_folder,
        exist_ok=True
    )


    # =========================
    # Create file path
    # =========================

    # Keep original filename for database
    file_name = os.path.basename(file.filename)

    # Create unique filename for physical storage
    unique_file_name = f"{uuid.uuid4()}_{file_name}"

    file_path = os.path.join(
        resume_folder,
        unique_file_name
)


    # =========================
    # Save file
    # =========================

    with open(file_path, "wb") as resume_file:

        resume_file.write(file_content)


    # =========================
    # Create Resume record
    # =========================

    new_resume = Resume.objects.create(
        candidate=candidate,
        file_name=file_name,
        file_type=file.content_type,
        file_path=file_path,
        file_size=file_size,
        extraction_status="Pending"
    )


    # =========================
    # Extract text
    # =========================

    try:

        if file.content_type == "application/pdf":

            extracted_text = extract_pdf_text(
                file_path
            )

        else:

            extracted_text = extract_docx_text(
                file_path
            )


        # =========================
        # Check extracted text
        # =========================

        if not extracted_text:

            new_resume.extracted_text = None
            new_resume.extraction_status = "Failed"

            new_resume.save()

            return {
                "message": "Resume uploaded but text extraction failed",
                "resume_id": new_resume.resume_id,
                "extraction_status": "Failed"
            }


        # =========================
        # Save extracted text
        # =========================

        new_resume.extracted_text = extracted_text
        new_resume.extraction_status = "Completed"

        new_resume.save()


        return {
            "message": "Resume uploaded and text extracted successfully",
            "resume": {
                "resume_id": new_resume.resume_id,
                "candidate_id": candidate.candidate_id,
                "candidate_name": candidate.full_name,
                "file_name": new_resume.file_name,
                "file_type": new_resume.file_type,
                "file_size": new_resume.file_size,
                "extraction_status": new_resume.extraction_status,
                "extracted_text": extracted_text,
                "uploaded_at": new_resume.uploaded_at
            }
        }


    except Exception as error:

        new_resume.extraction_status = "Failed"

        new_resume.save()

        return {
            "message": "Resume uploaded but text extraction failed",
            "resume_id": new_resume.resume_id,
            "extraction_status": "Failed",
            "error": str(error)
        }


# =========================
# GET ALL RESUMES
# =========================

@router.get("/")
def get_resumes():

    resumes = Resume.objects.all().order_by("-uploaded_at")

    resume_list = []

    for resume in resumes:

        resume_list.append({
            "resume_id": resume.resume_id,
            "candidate_id": resume.candidate_id,
            "candidate_name": resume.candidate.full_name,
            "file_name": resume.file_name,
            "file_type": resume.file_type,
            "file_size": resume.file_size,
            "extracted_text": resume.extracted_text,
            "extraction_status": resume.extraction_status,
            "uploaded_at": resume.uploaded_at
        })

    return {
        "message": "Resumes fetched successfully",
        "count": len(resume_list),
        "resumes": resume_list
    }


# =========================
# GET SINGLE RESUME
# =========================

@router.get("/{resume_id}")
def get_resume(resume_id: int):

    resume = Resume.objects.filter(
        resume_id=resume_id
    ).first()

    if not resume:
        return {
            "message": "Resume not found"
        }

    return {
        "message": "Resume fetched successfully",
        "resume": {
            "resume_id": resume.resume_id,
            "candidate_id": resume.candidate_id,
            "candidate_name": resume.candidate.full_name,
            "file_name": resume.file_name,
            "file_type": resume.file_type,
            "file_path": resume.file_path,
            "file_size": resume.file_size,
            "extracted_text": resume.extracted_text,
            "extraction_status": resume.extraction_status,
            "uploaded_at": resume.uploaded_at
        }
    }