from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from researchvault.database.session import get_db
from researchvault.core.security import decode_token
from researchvault.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    # If no token provided, create/return a default demo research user for seamless exploration
    if not token:
        demo_stmt = select(User).where(User.email == "researcher@researchvault.ai")
        demo_res = await db.execute(demo_stmt)
        demo_user = demo_res.scalar_one_or_none()
        if demo_user:
            return demo_user
        # Create default demo user
        from researchvault.core.security import get_password_hash
        new_demo = User(
            email="researcher@researchvault.ai",
            hashed_password=get_password_hash("ResearchVault2026!"),
            full_name="Ganesh",
            is_active=True,
            is_superuser=True
        )
        db.add(new_demo)
        await db.commit()
        await db.refresh(new_demo)
        return new_demo

    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive or non-existent user")
    return user
