"""
routes/auth.py
---------------
Authentication endpoints: signup and login.
"""

from fastapi import APIRouter, status

from app.schemas.auth import LoginRequest, SignupRequest, SignupResponse, TokenResponse, UserPublic
from app.services.auth_service import login_user, signup_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest) -> SignupResponse:
    """Register a new user and receive a JWT access token."""
    user_public, token_response = await signup_user(payload)
    return SignupResponse(user=user_public, token=token_response)


@router.post("/login", response_model=SignupResponse)
async def login(payload: LoginRequest) -> SignupResponse:
    """Authenticate an existing user and receive a JWT access token."""
    user_public, token_response = await login_user(payload)
    return SignupResponse(user=user_public, token=token_response)
