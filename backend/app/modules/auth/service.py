from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserOut
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.config import settings

class AuthService:
    @staticmethod
    async def register_user(db: AsyncSession, user_in: UserRegister) -> UserOut:
        # Check existing
        result = await db.execute(select(User).where(User.email == user_in.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
            
        new_user = User(
            email=user_in.email,
            password_hash=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            role=user_in.role,
            department=user_in.department
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return UserOut.model_validate(new_user)

    @staticmethod
    async def authenticate_user(db: AsyncSession, login_in: UserLogin) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == login_in.email))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(login_in.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )
            
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
