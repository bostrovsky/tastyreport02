from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import jwt, JWTError
from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Password hashing

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT helpers

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Any:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    secret = settings.REFRESH_SECRET_KEY or settings.SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_refresh_token(token: str) -> Any:
    secret = settings.REFRESH_SECRET_KEY or settings.SECRET_KEY
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
