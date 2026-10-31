from pwdlib import PasswordHash
import jwt
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from app.config import settings

password_hash = PasswordHash.recommended()

ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    return password_hash.verify(
        plain_password,
        hashed_password
    )


def create_access_token(
    user_id: int
) -> str:

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM
    )

    return token

def decode_access_token(
    token: str
) -> dict:

    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[ALGORITHM]
    )