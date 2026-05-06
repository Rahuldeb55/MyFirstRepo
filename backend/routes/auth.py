"""
Auth Routes — Guard authentication and session management.
Uses simple token-based auth with MAC address filtering support.
"""
import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import Guard
from schemas import GuardLogin, GuardTokenResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Simple in-memory token store (use Redis/JWT in production)
_active_tokens: dict = {}


def hash_password(password: str) -> str:
    """Simple SHA-256 hash for demo. Use bcrypt in production."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_guard_token(authorization: Optional[str] = Header(None)):
    """Dependency to verify guard authentication."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token provided")

    token = authorization.replace("Bearer ", "")
    if token not in _active_tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return _active_tokens[token]


@router.post("/login", response_model=GuardTokenResponse)
def guard_login(request: GuardLogin, db: Session = Depends(get_db)):
    """
    Authenticate a guard and return a session token.
    """
    guard = db.query(Guard).filter(Guard.id == request.guard_id).first()
    if not guard:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if guard.password_hash != hash_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not guard.is_active:
        raise HTTPException(status_code=403, detail="Guard account is deactivated")

    # Generate session token
    token = secrets.token_hex(32)
    _active_tokens[token] = {
        "guard_id": guard.id,
        "name": guard.name,
        "gate": guard.gate_assigned,
    }

    return GuardTokenResponse(
        access_token=token,
        guard_name=guard.name,
        gate=guard.gate_assigned,
    )


@router.post("/logout")
def guard_logout(authorization: Optional[str] = Header(None)):
    """Invalidate the guard's session token."""
    if authorization:
        token = authorization.replace("Bearer ", "")
        _active_tokens.pop(token, None)
    return {"message": "Logged out successfully"}


@router.get("/verify")
def verify_session(guard=Depends(verify_guard_token)):
    """Verify if the current token is valid."""
    return {"valid": True, "guard": guard}
