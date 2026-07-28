"""
services/auth_service.py
-------------------------
Business logic for user signup and login.
"""

from fastapi import HTTPException, status

from app.database import get_users_collection
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserPublic
from app.utils.security import create_access_token, hash_password, verify_password


async def signup_user(payload: SignupRequest) -> tuple[UserPublic, TokenResponse]:
    """
    Registers a new user:
      1. Ensures the email is not already taken.
      2. Hashes the password.
      3. Persists the user document.
      4. Issues a JWT access token.
    """
    users_collection = get_users_collection()

    existing_user = await users_collection.find_one({"email": payload.email})
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user_doc = {
        "full_name": payload.full_name,
        "email": payload.email,
        "hashed_password": hash_password(payload.password),
    }
    result = await users_collection.insert_one(user_doc)
    user_id = str(result.inserted_id)

    token, expires_in = create_access_token(subject=user_id)

    user_public = UserPublic(id=user_id, full_name=payload.full_name, email=payload.email)
    token_response = TokenResponse(access_token=token, expires_in=expires_in)

    return user_public, token_response


async def login_user(payload: LoginRequest) -> tuple[UserPublic, TokenResponse]:
    """
    Authenticates a user by email/password and issues a JWT access token.
    """
    users_collection = get_users_collection()

    user = await users_collection.find_one({"email": payload.email})
    if user is None or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user_id = str(user["_id"])
    token, expires_in = create_access_token(subject=user_id)

    user_public = UserPublic(id=user_id, full_name=user["full_name"], email=user["email"])
    token_response = TokenResponse(access_token=token, expires_in=expires_in)

    return user_public, token_response
