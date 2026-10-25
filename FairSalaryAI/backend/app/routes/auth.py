# FairSalary AI - Authentication Routes
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import (
    UserCreate, UserLogin, UserResponse, Token, RefreshTokenRequest
)
from app.security.password import hash_password, verify_password
from app.security.auth import (
    create_access_token, create_refresh_token, decode_token, verify_token_type
)
from app.dependencies import get_current_user, get_optional_user
from app.config import settings
from app.services.email_service import send_email
from datetime import datetime
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["Authentication"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if email already exists
    clean_email = user_data.email.strip().lower()
    existing_user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create user
    user = User(
        email=clean_email,
        full_name=user_data.full_name.strip(),
        hashed_password=hashed_password,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """Login and return JWT tokens."""
    # Find user
    clean_email = credentials.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )

    # Update last login
    from datetime import datetime
    user.last_login = __import__("datetime").datetime.utcnow()
    db.commit()

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    try:
        payload = decode_token(request.refresh_token)

        # Verify it's a refresh token
        if not verify_token_type(request.refresh_token, "refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # Check user still exists and is active
        user = db.query(User).filter(User.id == int(payload.sub)).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Email a password reset link to the registered user."""
    clean_email = request.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    email_sent = False
    if user:
        from jose import jwt as _jwt
        expire = datetime.utcnow() + timedelta(minutes=30)
        token = _jwt.encode(
            {"sub": str(user.id), "email": user.email, "type": "reset", "exp": expire},
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        plain_body = (
            f"Hi {user.full_name},\n\n"
            f"You requested to reset your password for FairSalary AI.\n\n"
            f"Click the link below to set your new password (valid for 30 minutes):\n"
            f"{reset_url}\n\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"Best regards,\nFairSalary AI Team"
        )
        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 580px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #0284c7; margin-top: 0;">FairSalary AI - Password Reset</h2>
            <p style="color: #334155; font-size: 15px;">Hi <strong>{user.full_name}</strong>,</p>
            <p style="color: #334155; font-size: 15px;">We received a request to reset your password. Click the button below to choose your new password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background-color: #0284c7; color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 6px; font-weight: 600; font-size: 15px; display: inline-block;">Reset Password</a>
            </div>
            <p style="color: #64748b; font-size: 13px;">This link is valid for 30 minutes. If you did not make this request, you can safely ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
            <p style="color: #94a3b8; font-size: 12px; word-break: break-all;">If the button does not work, copy and paste this link into your browser:<br/><a href="{reset_url}" style="color: #0284c7;">{reset_url}</a></p>
        </div>
        """
        email_sent = send_email(
            user.email,
            "FairSalary AI - Reset Your Password",
            plain_body,
            html_body=html_body,
        )
    return {
        "message": "If that email is registered, a password reset link has been sent to your email address. Please check your inbox.",
        "email_sent": email_sent,
    }


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using the emailed token."""
    try:
        from jose import jwt as _jwt
        raw = _jwt.decode(request.token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if raw.get("type") != "reset":
            raise HTTPException(status_code=400, detail="Invalid token")
        user_id = int(raw["sub"])
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = hash_password(request.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.post("/logout")
async def logout(response: Response):
    """Logout (client should delete tokens)."""
    return {"message": "Successfully logged out"}
