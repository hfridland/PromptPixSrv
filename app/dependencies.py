import jwt

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:
        payload = decode_access_token(
            token
        )

        user_id = int(
            payload["sub"]
        )

    except (
        jwt.InvalidTokenError,
        KeyError,
        ValueError,
    ):
        raise credentials_exception

    db_user = db.get(
        User,
        user_id
    )

    if db_user is None:
        raise credentials_exception

    return db_user