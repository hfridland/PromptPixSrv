from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.schemas.users import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserUpdatePartial,
)

from app.dependencies import get_current_user
from app.models import User
from app.services import users as user_service

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("",
         response_model=list[UserResponse])
def get_users(
        min_age: int | None = None,
        max_age: int | None = None,
        name: str | None = None,
        limit: int = Query(
            default=20,
            ge=1,
            le=100
        ),
        offset: int = Query(
            default=0,
            ge=0
        ),
        db: Session = Depends(get_db)
):
    return user_service.get_users(min_age, max_age, name, limit, offset, db)

@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(
        get_current_user
    )
):
    return current_user

@router.get(
    "/{user_id}",
    response_model=UserResponse
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user
# def get_me(
#     current_user: User = Depends(
#         get_current_user
#     )
# ):
#     return current_user

@router.post(
    "",
    response_model=UserResponse
)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    try:
        return user_service.create_user(
            db,
            user
        )
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="User already exists"
        )

@router.put("/{user_id}",
         response_model=UserResponse)
def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db)
):
    return user_service.update_user(user_id, user, db)

@router.patch("/{user_id}",
           response_model=UserResponse)
def patch_user(
    user_id: int,
    user: UserUpdatePartial,
    db: Session = Depends(get_db)
):
    return user_service.patch_user(user_id, user, db)

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):
    return user_service.delete_user(user_id, db)
