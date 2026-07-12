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
from api.schemas import LoginRequest, TokenResponse, RegisterRequest

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register")
def register(payload: RegisterRequest):
    """
    Registers a new user account with a specified role.
    """
    valid_roles = ["Fleet Manager", "Driver", "Safety Officer", "Financial Analyst"]
    if payload.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )

    # Hash the password
    password_hash = auth.hash_password(payload.password)

    # Insert user record
    with database.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (payload.email,))
            if cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered."
                )
            
            try:
                cur.execute(
                    """
                    INSERT INTO users (email, password_hash, role)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (payload.email, password_hash, payload.role)
                )
                user_id = cur.fetchone()["id"]
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database error: {e}"
                )

    return {
        "message": "User successfully registered.",
        "user_id": user_id,
        "email": payload.email,
        "role": payload.role
    }


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
