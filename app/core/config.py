from pydantic_settings import BaseSettings
from pydantic import EmailStr
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    REFRESH_SECRET_KEY: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    ENCRYPTION_KEY: str = Field(..., json_schema_extra={"env": "ENCRYPTION_KEY"})
    # Allow test credentials for TastyTrade
    TASTYTRADE_USERNAME: Optional[str] = None
    TASTY_PASSWORD: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def database_uri(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
        )

settings = Settings()
