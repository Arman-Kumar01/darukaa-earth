"""Authentication endpoints: register, login, me."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.auth_service import authenticate_user, get_current_user, register_user

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new user account",
    description="Creates a new user and returns a JWT access token. The user is automatically authenticated after registration.",
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    return register_user(db, payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive a JWT token",
    description="Validates email and password, returns a JWT access token valid for 24 hours.",
)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    return authenticate_user(db, payload.email, payload.password)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
    description="Returns user profile information for the bearer of a valid JWT token.",
)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
