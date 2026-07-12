"""
TransitOps Authentication & RBAC Module (core/auth.py)
------------------------------------------------------
Provides:
  - bcrypt password hashing / verification
  - JWT access token creation / decoding
  - FastAPI dependency: get_current_user  (validates any Bearer token)
  - FastAPI dependency factory: require_roles(*roles)  (enforces RBAC)

Configure SECRET_KEY via the SECRET_KEY environment variable.
Default value is a placeholder — CHANGE IT before any real deployment.

Author: Developer 1 (Senior Backend Engineer)
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────

SECRET_KEY: str = os.getenv(
    "SECRET_KEY",
    "transitops-hackathon-insecure-default-key-change-in-production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# bcrypt context — automatically handles salting and stretching
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FastAPI Bearer token extractor (reads Authorization: Bearer <token>)
_bearer_scheme = HTTPBearer()


# ──────────────────────────────────────────────────────────────
# Password Utilities
# ──────────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Returns a bcrypt hash of the given plaintext password."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Returns True if plain_password matches the stored bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


# ──────────────────────────────────────────────────────────────
# JWT Utilities
# ──────────────────────────────────────────────────────────────

def create_access_token(
    user_id: int,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates a signed JWT access token containing:
      - sub   : user email (standard JWT subject claim)
      - role  : the user's TransitOps role
      - uid   : the user's database primary key
      - exp   : expiry timestamp (UTC)
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    payload = {
        "sub": email,
        "role": role,
        "uid": user_id,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token_payload(token: str) -> dict:
    """
    Decodes and validates a JWT, raising HTTP 401 on any failure.
    Internal helper — use get_current_user() in routes instead.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ──────────────────────────────────────────────────────────────
# FastAPI Dependencies
# ──────────────────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """
    FastAPI dependency. Extracts the JWT from the Authorization header,
    validates it, and returns the decoded payload as a dict:
      { "sub": email, "role": role, "uid": user_id }

    Raises HTTP 401 if the token is missing, malformed, or expired.
    """
    return _decode_token_payload(credentials.credentials)


def require_roles(*allowed_roles: str):
    """
    FastAPI dependency factory for role-based access control.

    Usage:
      @app.get("/api/dispatch")
      def dispatch(user=Depends(require_roles("Fleet Manager"))):
          ...

    Raises HTTP 401 if the token is invalid.
    Raises HTTP 403 if the user's role is not in allowed_roles.
    Returns the current user dict on success.
    """
    def _checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. "
                    f"Required role(s): {', '.join(allowed_roles)}. "
                    f"Your role: '{current_user.get('role')}'."
                ),
            )
        return current_user
    return _checker


# ──────────────────────────────────────────────────────────────
# Convenience Role Constants (import-friendly)
# ──────────────────────────────────────────────────────────────

FLEET_MANAGER = "Fleet Manager"
DRIVER = "Driver"
SAFETY_OFFICER = "Safety Officer"
FINANCIAL_ANALYST = "Financial Analyst"

ALL_ROLES = (FLEET_MANAGER, DRIVER, SAFETY_OFFICER, FINANCIAL_ANALYST)
