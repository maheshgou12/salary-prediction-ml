# FairSalary AI - Authentication Routes
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
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

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create user
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
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
    user = db.query(User).filter(User.email == credentials.email).first()
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
        data={"sub": user.id, "email": user.email, "role": user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id, "email": user.email, "role": user.role}
    )

    # Update last login
    from datetime import datetime
    user.last_login = __import__("datetime").datetime.utcnow()
    db.commit()

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60  # 30 minutes in seconds
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
        user = db.query(User).filter(User.id == payload.sub).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new tokens
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )
        new_refresh_token = create_refresh_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=30 * 60
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.post("/logout")
async def logout(response: Response):
    """Logout (client should delete tokens)."""
    return {"message": "Successfully logged out"}