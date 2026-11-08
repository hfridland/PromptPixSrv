from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.users import UserLogin
from app.services.users import get_user_by_email, get_user_by_name
from app.security import verify_password, create_access_token
from app.schemas.auth import TokenResponse


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/login",  response_model=TokenResponse)
def login(
    # user: UserLogin,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    db_user = get_user_by_email(
        db,
        form_data.username,
        # user.email
    )

    if db_user is None:
        db_user = get_user_by_name(db, form_data.username)


    if db_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if db_user.password_hash is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        # user.password,
        form_data.password,
        db_user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(
        db_user.id
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

