from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import decode_access_token
from app.crud.crud_user import get_user_by_email
from app.db.models.user import User
from jose import JWTError
from typing import Optional

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    auth_header: Optional[str] = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = auth_header.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload["sub"]
    # We need to get user by id, but our CRUD only has get_user_by_email. Let's add get_user_by_id inline for now.
    from sqlalchemy.future import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user
