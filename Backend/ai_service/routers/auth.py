from fastapi import APIRouter
from pydantic import BaseModel
from services.auth_utils import create_access_token
from accounts.models import User
from django.contrib.auth.hashers import make_password, check_password


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


# =========================
# REGISTER
# =========================

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "recruiter"


@router.post("/register")
def register_user(user: RegisterRequest):

    # Check if email already exists
    existing_user = User.objects.filter(
        email=user.email
    ).first()

    if existing_user:
        return {
            "message": "User already exists",
            "user": {
                "user_id": existing_user.user_id,
                "full_name": existing_user.full_name,
                "email": existing_user.email,
                "role": existing_user.role,
                "is_active": existing_user.is_active
            }
        }

    # Create new user
    new_user = User.objects.create(
        full_name=user.full_name,
        email=user.email,
        password_hash=make_password(user.password),
        role=user.role,
        is_active=True
    )

    return {
        "message": "User registered successfully",
        "user_id": new_user.user_id
    }


# =========================
# LOGIN
# =========================

class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login_user(user: LoginRequest):

    # Find user by email
    existing_user = User.objects.filter(
        email=user.email
    ).first()

    # User not found
    if not existing_user:
        return {
            "message": "Invalid email or password"
        }

    # Check password
    password_correct = check_password(
        user.password,
        existing_user.password_hash
    )

    if not password_correct:
        return {
            "message": "Invalid email or password"
        }

    # Check account status
    if not existing_user.is_active:
        return {
            "message": "User account is inactive"
        }

    # Create JWT token
    token = create_access_token(
        existing_user.user_id,
        existing_user.role
    )

    # Login successful
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "user_id": existing_user.user_id,
            "full_name": existing_user.full_name,
            "email": existing_user.email,
            "role": existing_user.role,
            "is_active": existing_user.is_active
        }
    }