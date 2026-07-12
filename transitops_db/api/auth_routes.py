"""
TransitOps Auth Routes (api/auth_routes.py)
-------------------------------------------
Endpoints:
  POST /api/auth/login  — validates credentials, returns JWT
  GET  /api/auth/me     — returns current user info from token

Author: Developer 1 (Senior Backend Engineer)
"""

import os
import sys

from fastapi import APIRouter, Depends, HTTPException, status

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import database, auth
from api.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    """
    Authenticates a user with email and password.
    Returns a signed JWT access token valid for 24 hours.

    Include the token in all subsequent requests:
      Authorization: Bearer <access_token>
    """
    # Fetch user record from database
    with database.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, password_hash, role FROM users WHERE email = %s",
                (payload.email,)
            )
            user = cur.fetchone()

    # Validate existence and password
    if not user or not auth.verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue JWT
    token = auth.create_access_token(
        user_id=user["id"],
        email=user["email"],
        role=user["role"],
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "email": user["email"],
    }


@router.get("/me")
def get_me(current_user: dict = Depends(auth.get_current_user)):
    """
    Returns the currently authenticated user's identity decoded from their JWT.
    No database query — reads directly from the validated token payload.
    """
    return {
        "user_id": current_user.get("uid"),
        "email": current_user.get("sub"),
        "role": current_user.get("role"),
    }
