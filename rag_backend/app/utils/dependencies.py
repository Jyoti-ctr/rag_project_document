"""
utils/dependencies.py
----------------------
Reusable FastAPI dependencies, primarily for extracting and validating
the current authenticated user from the JWT bearer token.
"""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.database import get_users_collection
from app.utils.security import decode_access_token

# Token endpoint used for OpenAPI docs "Authorize" button.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Decodes the bearer token, loads the corresponding user from MongoDB,
    and returns the user document. Raises 401 on any failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        object_id = ObjectId(user_id)
    except (InvalidId, TypeError):
        raise credentials_exception

    users_collection = get_users_collection()
    user = await users_collection.find_one({"_id": object_id})
    if user is None:
        raise credentials_exception

    return user


async def get_current_user_id(current_user: dict = Depends(get_current_user)) -> str:
    """Convenience dependency that returns just the user's string ID."""
    return str(current_user["_id"])
