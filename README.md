# TalentIQ Backend

TalentIQ is an AI-powered recruitment support system designed to help recruiters screen resumes, evaluate candidate-job fit, identify skill gaps, generate candidate summaries, rank candidates, and prepare interview questions.

This README documents the **backend** implemented for TalentIQ.

---

## 1. Backend Overview

TalentIQ uses a hybrid backend architecture:

- **Django** → database models, schema, migrations, and Django Admin
- **FastAPI** → REST APIs and application/business logic
- **MySQL** → relational database
- **Google Gemini AI** → NLP skill extraction, semantic matching, summaries, and interview-question generation
- **JWT** → authentication and authorization
- **Pypdf / python-docx** → resume text extraction

### Architecture

```text
React Frontend
      |
      | HTTP / REST API
      v
FastAPI (8001)
      |
      +----------------------+
      |                      |
      v                      v
Django ORM              AI Services
      |                      |
      v                      v
MySQL Database         Google Gemini
```

Django and FastAPI share the same Django models and MySQL database.

---

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| Django | ORM, database models, migrations, admin |
| FastAPI | REST API layer |
| MySQL | Relational database |
| PyJWT | JWT authentication |
| Google Gemini | AI/NLP functionality |
| Pypdf | PDF resume text extraction |
| python-docx | DOCX resume text extraction |
| Pydantic | API validation |
| Uvicorn | FastAPI server |
| python-dotenv | Environment variables |
| React/Vite | Frontend client |
| Axios | Frontend API communication |

---

## 3. Project Structure

```text
Backend/
├── .venv/
├── .env
│
├── HireSense/
│   ├── accounts/
│   ├── jobs/
│   ├── candidates/
│   ├── resumes/
│   ├── skills/
│   ├── analysis/
│   ├── HireSense/
│   ├── media/
│   │   └── resumes/
│   └── manage.py
│
└── ai_service/
    ├── main.py
    ├── routers/
    │   ├── auth.py
    │   ├── jobs.py
    │   ├── candidates.py
    │   ├── resumes.py
    │   ├── skills.py
    │   └── analysis.py
    └── services/
        ├── auth_utils.py
        ├── skill_extractor.py
        ├── ai_skill_extractor.py
        ├── semantic_matcher.py
        ├── ai_summary_generator.py
        └── interview_generator.py
```

---

## 4. Database

Database name:

```text
talentiq_db
```

Main tables:

```text
users
jobs
candidates
resumes
skills
candidate_skills
job_skills
resume_analysis
skill_gaps
candidate_scores
interview_questions
interview_sessions
```

Django models are the source of truth for the database schema, relationships, constraints, and migrations.

---

## 5. Database Models

### Users

Stores recruiter and admin accounts.

Important fields:

- `user_id`
- `full_name`
- `email`
- `password_hash`
- `role`
- `is_active`
- `created_at`
- `updated_at`

Roles:

```text
recruiter
admin
```

Passwords are stored using Django password hashing.

### Jobs

Stores job postings.

Important fields include job title, department, location, employment type, description, experience range, recruiter, status, and timestamps.

Employment types:

```text
Full-time
Part-time
Internship
Contract
```

Job statuses:

```text
Draft
Active
Closed
```

### Candidates

Stores candidate information such as name, email, phone, location, total experience, education, LinkedIn, and GitHub.

Candidate email is unique.

### Resumes

Stores uploaded resume metadata and extracted text.

Important fields:

- `resume_id`
- `candidate_id`
- `file_name`
- `file_type`
- `file_path`
- `file_size`
- `extracted_text`
- `extraction_status`
- `uploaded_at`

Extraction status:

```text
Pending
Completed
Failed
```

Uploaded resumes are stored under:

```text
HireSense/media/resumes/
```

A UUID is used for the physical file name to avoid collisions while the original file name remains stored in the database.

PDF and DOCX text extraction are supported. Scanned PDFs may require OCR in a future version.

### Skills

Stores the master skill list.

Examples:

```text
Python
Django
FastAPI
Java
JavaScript
React
HTML
CSS
Bootstrap
MySQL
PostgreSQL
MongoDB
SQL
Git
GitHub
Docker
AWS
REST API
Machine Learning
NLP
Pandas
NumPy
Flask
C++
C#
TypeScript
```

Skill names are unique and can also contain category and alias information.

### Candidate Skills

Connects candidates with skills and stores:

- proficiency
- years of experience
- evidence text
- source
- confidence score

A unique candidate-skill constraint prevents duplicate mappings.

### Job Skills

Connects jobs with skills and stores:

- importance (`Required` / `Preferred`)
- minimum experience
- weight

### Resume Analysis

Stores the result of analyzing a resume against a job.

Scores include:

- semantic score
- experience score
- education score
- skill match score
- resume quality score
- overall score

A unique resume-job constraint prevents duplicate analyses for the same combination.

### Skill Gaps

Stores missing or partially matched skills.

Gap types:

```text
Missing
Partial
```

Severity values:

```text
Low
Medium
High
```

### Candidate Scores

Stores individual scoring components, final score, ranking, and scoring version.

### Interview Questions

Stores generated interview questions with type, difficulty, related skill, reason, and generation source.

Question types:

```text
Technical
Behavioral
Experience
Skill Gap
```

### Interview Sessions

Stores interview scheduling and status information.

Statuses:

```text
Scheduled
In Progress
Completed
Cancelled
```

The system records `started_at` when an interview moves to `In Progress` and `ended_at` when it moves to `Completed`.

---

## 6. Authentication and Authorization

TalentIQ uses JWT-based authentication.

### Authentication Flow

```text
Register/Login
     ↓
Validate credentials
     ↓
Generate JWT
     ↓
Frontend stores token
     ↓
Bearer token sent with API requests
     ↓
Protected API validates token
```

JWT payload contains:

- user ID
- user role
- expiration time

Token lifetime:

```text
24 hours
```

Protected requests use:

```http
Authorization: Bearer <JWT_TOKEN>
```

Authentication helpers are implemented in:

```text
ai_service/services/auth_utils.py
```

---

## 7. Role-Based Access Control

### Recruiter

Recruiters can access recruitment functionality including jobs, candidates, resumes, skills, analysis, AI features, and interviews.

### Admin

Admins have recruiter-level access plus administrative functionality.

Creating master skills is restricted to the `admin` role.

The reusable `require_role()` dependency is used for role checks.

---

## 8. API Base URLs

FastAPI:

```text
http://127.0.0.1:8001
```

Swagger:

```text
http://127.0.0.1:8001/docs
```

Django Admin:

```text
http://127.0.0.1:8000/admin/
```

---

## 9. Authentication APIs

### Register

```http
POST /api/auth/register
```

Example request:

```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "password": "password123",
  "role": "recruiter"
}
```

### Login

```http
POST /api/auth/login
```

Example request:

```json
{
  "email": "john@example.com",
  "password": "password123"
}
```

Successful login returns a JWT token and user information.

---

## 10. Job APIs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/jobs/` | Create job |
| GET | `/api/jobs/` | Get all jobs |
| GET | `/api/jobs/{job_id}` | Get one job |
| PUT | `/api/jobs/{job_id}` | Update job |
| PATCH | `/api/jobs/{job_id}/close` | Close job |
| POST | `/api/jobs/skills` | Add job skill |
| GET | `/api/jobs/{job_id}/skills` | Get job skills |

All job APIs require authentication.

---

## 11. Candidate APIs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/candidates/` | Create candidate |
| GET | `/api/candidates/` | Get all candidates |
| GET | `/api/candidates/{candidate_id}` | Get one candidate |

Duplicate candidates are prevented using email.

---

## 12. Resume APIs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/resumes/upload` | Upload resume |
| GET | `/api/resumes/` | Get all resumes |
| GET | `/api/resumes/{resume_id}` | Get one resume |

Resume upload uses `multipart/form-data` with:

```text
candidate_id
file
```

Processing flow:

```text
Upload
  ↓
Save file
  ↓
Extract text
  ↓
Update extraction status
  ↓
Resume ready for analysis
```

---

## 13. Skill APIs

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| GET | `/api/skills/` | Get master skills | Recruiter/Admin |
| POST | `/api/skills/` | Create master skill | Admin only |
| POST | `/api/skills/candidate` | Add candidate skill | Recruiter/Admin |
| GET | `/api/skills/candidate/{candidate_id}` | Get candidate skills | Recruiter/Admin |
| POST | `/api/skills/extract/{resume_id}` | Rule-based extraction | Recruiter/Admin |
| POST | `/api/skills/extract-ai/{resume_id}` | AI extraction | Recruiter/Admin |

---

## 14. AI Skill Extraction

TalentIQ uses Google Gemini to extract skills from resumes.

The model receives the resume text and the master skill list.

The system instructs the model to:

1. Extract only skills from the master list.
2. Use exact skill names.
3. Provide evidence from the resume.
4. Estimate proficiency only when supported.
5. Estimate years of experience only when enough evidence exists.
6. Return confidence from 0–100.
7. Never invent unsupported skills.

Output fields:

```text
skill_name
proficiency
years_experience
evidence_text
confidence_score
```

Implementation:

```text
ai_service/services/ai_skill_extractor.py
```

Model currently used:

```text
gemini-3.5-flash-lite
```

---

## 15. Analysis APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/analysis/` | Get analyses |
| GET | `/api/analysis/{analysis_id}` | Get one analysis |
| POST | `/api/analysis/full/{resume_id}/{job_id}` | Run complete AI analysis |
| POST | `/api/analysis/recalculate/{analysis_id}` | Recalculate scores |
| POST | `/api/analysis/summary/generate/{analysis_id}` | Generate AI summary |
| POST | `/api/analysis/questions/generate/{analysis_id}` | Generate AI questions |

All analysis APIs require authentication.

---

## 16. Full AI Analysis Workflow

The main endpoint is:

```http
POST /api/analysis/full/{resume_id}/{job_id}
```

It automates the complete pipeline:

```text
Resume
  ↓
AI Skill Extraction
  ↓
Candidate Skills
  ↓
Job Skills
  ↓
Skill Matching
  ↓
Experience Scoring
  ↓
Semantic AI Matching
  ↓
Resume Quality Scoring
  ↓
Overall Score
  ↓
Candidate Ranking
  ↓
Skill Gap Detection
  ↓
AI Summary
  ↓
AI Interview Questions
```

The endpoint returns analysis information including scores, summary, interview questions, and skill gaps.

---

## 17. Semantic Matching

TalentIQ uses real Gemini embeddings for semantic resume-job matching.

Embedding model:

```text
gemini-embedding-001
```

Process:

```text
Resume text
    ↓
Gemini embedding

Job description
    ↓
Gemini embedding

Both embeddings
    ↓
Cosine similarity
    ↓
Semantic score (0–100)
```

Implementation:

```text
ai_service/services/semantic_matcher.py
```

The semantic score is generated from actual AI embeddings rather than a hardcoded value.

---

## 18. Candidate Scoring

Current weighted scoring formula:

```text
Overall Score =
    Skill Match × 0.50
  + Experience × 0.20
  + Semantic Match × 0.20
  + Resume Quality × 0.10
```

Example:

```text
Skill Match       = 100
Experience        = 100
Semantic Match    = 63.18
Resume Quality    = 100

Overall Score =
    100 × 0.50
  + 100 × 0.20
  + 63.18 × 0.20
  + 100 × 0.10

Overall Score = 92.64
```

Current scoring version:

```text
v6-ai-semantic-score
```

The scoring version is stored for traceability.

---

## 19. Candidate Ranking

Candidates are ranked per job using their final scores.

```text
Highest score → Rank 1
Next score    → Rank 2
Next score    → Rank 3
...
```

Rankings are recalculated when candidate scores are created or recalculated.

---

## 20. Skill Gap Detection

Skill gaps are detected by comparing:

```text
Required Job Skills
       vs
Candidate Skills
```

Possible gap types:

```text
Missing
Partial
```

A gap can contain:

```text
Candidate Level
Required Level
Explanation
Severity
```

This makes candidate evaluation more explainable to recruiters.

---

## 21. AI Candidate Summary

Gemini generates a concise recruiter-friendly candidate evaluation.

The prompt considers:

- candidate
- job
- matched skills
- missing skills
- skill score
- experience score
- semantic score
- resume quality
- overall score
- resume content

Requirements include 3–5 professional sentences, relevant strengths, important gaps, overall suitability, and no invented experience or skills.

Implementation:

```text
ai_service/services/ai_summary_generator.py
```

API:

```http
POST /api/analysis/summary/generate/{analysis_id}
```

---

## 22. AI Interview Questions

TalentIQ generates exactly five questions for an analyzed candidate:

```text
2 × Technical
1 × Behavioral
1 × Experience
1 × Skill Gap
```

Each question can include:

- question text
- type
- difficulty
- related skill
- reason
- generation source

API:

```http
POST /api/analysis/questions/generate/{analysis_id}
```

Implementation:

```text
ai_service/services/interview_generator.py
```

Current generation model:

```text
gemini-3.5-flash-lite
```

---

## 23. Interview Session APIs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/analysis/interviews/` | Create interview session |
| GET | `/api/analysis/interviews/` | Get all sessions |
| GET | `/api/analysis/interviews/{session_id}` | Get one session |
| PATCH | `/api/analysis/interviews/{session_id}` | Update schedule/notes |
| PATCH | `/api/analysis/interviews/{session_id}/status` | Update interview status |

Supported statuses:

```text
Scheduled
In Progress
Completed
Cancelled
```

When status becomes `In Progress`, `started_at` is recorded.

When status becomes `Completed`, `ended_at` is recorded.

---

## 24. Environment Variables

Create:

```text
Backend/.env
```

Example:

```env
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET_KEY=your_secret_key
```

Django database settings use the MySQL database:

```text
Database: talentiq_db
Host: localhost
Port: 3306
User: root
```

Never commit real API keys, JWT secrets, or database passwords.

---

## 25. Installation

Open PowerShell:

```powershell
cd D:\TALENT_IQ\Backend
```

Activate the shared backend virtual environment:

```powershell
.venv\Scripts\activate
```

Install dependencies as needed:

```powershell
pip install django fastapi uvicorn pydantic PyJWT python-dotenv python-multipart pypdf python-docx google-genai
```

If the project already has these packages installed, reinstalling is not required.

---

## 26. Database Setup

Create the database in MySQL:

```sql
CREATE DATABASE talentiq_db;
```

Configure database credentials in Django settings.

Then run migrations:

```powershell
cd D:\TALENT_IQ\Backend\HireSense
python manage.py makemigrations
python manage.py migrate
```

---

## 27. Django Admin

Create a Django admin account if required:

```powershell
python manage.py createsuperuser
```

Start Django:

```powershell
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/admin/
```

Django Admin is used for database administration and backend data management.

---

## 28. Start FastAPI

Open another terminal:

```powershell
cd D:\TALENT_IQ\Backend
.venv\Scripts\activate
cd ai_service
python -m uvicorn main:app --reload --port 8001
```

FastAPI:

```text
http://127.0.0.1:8001
```

Swagger:

```text
http://127.0.0.1:8001/docs
```

---

## 29. Swagger Authentication

For protected endpoints:

1. Call `POST /api/auth/login`.
2. Copy the returned JWT token.
3. Click **Authorize** in Swagger.
4. Enter:

```text
Bearer <YOUR_TOKEN>
```

5. Execute protected endpoints.

---

## 30. CORS

FastAPI is configured to allow the React/Vite development frontend:

```text
http://localhost:5173
```

This allows the browser frontend to call the backend during development.

---

## 31. End-to-End Recruitment Workflow

```text
1. Recruiter registers/logs in
          ↓
2. JWT token generated
          ↓
3. Recruiter creates a job
          ↓
4. Job skills are added
          ↓
5. Candidate is created
          ↓
6. Candidate resume is uploaded
          ↓
7. Resume text is extracted
          ↓
8. AI extracts candidate skills
          ↓
9. Resume is analyzed against job
          ↓
10. Skill match calculated
          ↓
11. Experience score calculated
          ↓
12. Semantic AI score calculated
          ↓
13. Resume quality calculated
          ↓
14. Overall score calculated
          ↓
15. Candidate ranking updated
          ↓
16. Skill gaps identified
          ↓
17. AI candidate summary generated
          ↓
18. AI interview questions generated
          ↓
19. Recruiter schedules interview
          ↓
20. Interview status is managed
```

---

## 32. Backend Security

Implemented security features:

- JWT authentication
- Password hashing
- Protected recruitment APIs
- Role-based authorization
- Admin-only master skill creation
- Token expiration
- Environment-based secrets
- Duplicate email prevention
- Foreign-key relationships
- Database constraints

---

## 33. Data Integrity

Important database protections include:

- unique user email
- unique candidate email
- unique skill name
- unique candidate-skill combination
- unique resume-job analysis combination
- foreign keys
- controlled status fields
- Django migrations

---

## 34. Error Handling

The backend handles common cases such as:

```text
Invalid login
Inactive account
Invalid/expired JWT
Unauthorized request
Forbidden role
Resource not found
Duplicate candidate
Duplicate user
Invalid resume
Resume extraction failure
Missing Gemini API key
```

Relevant HTTP status codes such as `401`, `403`, and `404` are returned where appropriate.

---

## 35. Testing Completed

The backend workflow has been tested through FastAPI Swagger.

Tested functionality includes:

- user registration
- user login
- password hashing/checking
- JWT authentication
- protected APIs
- role-based access
- job CRUD
- job closing
- job skills
- candidate creation/retrieval
- resume upload
- PDF/DOCX text extraction
- master skills
- rule-based skill extraction
- AI skill extraction
- resume analysis
- Gemini semantic scoring
- candidate scoring
- candidate ranking
- AI summary generation
- AI interview-question generation
- interview session creation
- interview session update
- interview status management
- full AI analysis workflow

The complete AI analysis flow has successfully produced semantic score, skill score, experience score, resume-quality score, overall score, AI summary, interview questions, and skill-gap information.

---

## 36. Design Decisions

### Django owns the database

Django models are responsible for:

```text
Tables
Relationships
Constraints
Migrations
Admin
```

### FastAPI owns the API layer

FastAPI is responsible for:

```text
REST endpoints
Authentication
Authorization
Business logic
AI workflow
```

### AI logic is separated into services

AI functionality is kept in separate service modules instead of putting all AI logic inside API routers. This keeps the code easier to maintain.

---

## 37. Development Ports

| Service | Port |
|---|---:|
| Django | 8000 |
| FastAPI | 8001 |
| React/Vite | 5173 |
| MySQL | 3306 |

---

## 38. Running the Backend

### Terminal 1 — Django

```powershell
cd D:\TALENT_IQ\Backend
.venv\Scripts\activate
cd HireSense
python manage.py runserver
```

### Terminal 2 — FastAPI

```powershell
cd D:\TALENT_IQ\Backend
.venv\Scripts\activate
cd ai_service
python -m uvicorn main:app --reload --port 8001
```

Then open:

```text
Django Admin: http://127.0.0.1:8000/admin/
FastAPI:      http://127.0.0.1:8001/
Swagger:      http://127.0.0.1:8001/docs
```

---

## 39. Frontend Integration Contract

The backend is ready to be consumed by the React frontend through REST APIs.

Frontend integration should:

1. Register/login through `/api/auth`.
2. Store the JWT token.
3. Send the token using the Bearer authorization header.
4. Use Axios/API service functions for backend communication.
5. Upload resumes using `multipart/form-data`.
6. Trigger `/api/analysis/full/{resume_id}/{job_id}` for the complete AI workflow.
7. Display scores, ranking, summaries, skill gaps, and interview questions.
8. Manage interview sessions through the interview APIs.

Communication flow:

```text
React
  ↓
Axios
  ↓
FastAPI
  ↓
Django ORM + AI Services
  ↓
MySQL + Gemini
```

---

## 40. Future Improvements

Possible future improvements:

- OCR for scanned resumes
- improved education scoring
- improved resume quality scoring
- better job-skill weight configuration
- candidate filtering/search
- pagination
- refresh tokens
- more granular permissions
- background processing for long AI jobs
- production deployment
- logging and monitoring
- automated backend test suite
- stronger AI model/version tracking

---

## 41. Git and Security

Recommended `.gitignore` entries:

```text
.env
Backend/.env
__pycache__/
*.pyc
.venv/
Backend/.venv/
```

Never commit:

```text
GEMINI_API_KEY
JWT_SECRET_KEY
MySQL password
```

---

## 42. Project Status

### Backend: Completed

Core backend functionality implemented:

- database schema
- Django models
- migrations
- Django Admin
- FastAPI application
- authentication
- JWT authorization
- role-based access control
- job management
- candidate management
- resume upload
- resume text extraction
- master skills
- AI skill extraction
- semantic AI matching
- candidate scoring
- candidate ranking
- skill-gap detection
- AI candidate summary
- AI interview questions
- interview session management
- CORS configuration
- frontend-ready REST APIs

The next major phase is **React frontend integration with the completed backend APIs**.

---

## 43. Project Information

**Project:** TalentIQ

**Purpose:** AI-powered recruitment and resume screening system

**Backend:** Django + FastAPI + MySQL

**AI:** Google Gemini

**Frontend:** React / Vite
