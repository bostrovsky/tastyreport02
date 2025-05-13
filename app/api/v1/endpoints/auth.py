from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.schemas.token import Token, RefreshToken
from app.crud.crud_user import get_user_by_email, create_user, update_user_last_login
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_refresh_token
from fastapi import Body
from app.api.v1.deps import get_current_active_user
from sqlalchemy.future import select
from app.db.models.user import User
import inspect

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await create_user(db, user_in)
    print('DEBUG /register signature at import:', inspect.signature(register))
    return user

@router.post("/login", response_model=Token)
async def login(
    email: str = Body(...),
    password: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    await update_user_last_login(db, user)
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id), "role": user.role})
    return Token(access_token=access_token, refresh_token=refresh_token)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    # For stateless JWT, logout is handled client-side (delete tokens)
    return

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    body: RefreshToken,
    db: AsyncSession = Depends(get_db),
):
    payload = decode_refresh_token(body.refresh_token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id), "role": user.role})
    return Token(access_token=access_token, refresh_token=refresh_token)

@router.get("/me", response_model=UserRead)
async def get_me(current_user = Depends(get_current_active_user)):
    return current_user

@router.post("/register-user", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await create_user(db, user_in)
    return user
