"""
schemas/auth.py
----------------
Pydantic request/response models for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, examples=["Jane Doe"])
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserPublic(BaseModel):
    id: str
    full_name: str
    email: EmailStr


class SignupResponse(BaseModel):
    user: UserPublic
    token: TokenResponse
