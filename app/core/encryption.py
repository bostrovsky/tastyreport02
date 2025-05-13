from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings

fernet = Fernet(settings.ENCRYPTION_KEY.encode())

def encrypt(text: str) -> str:
    return fernet.encrypt(text.encode()).decode()

def decrypt(token: str) -> str:
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        raise ValueError("Invalid encryption token")
