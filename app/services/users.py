from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import User
from app.schemas.users import UserCreate, UserUpdate, UserUpdatePartial
from app.security import hash_password

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def get_user_by_email(
    db: Session,
    email: str
) -> User | None:

    stmt = select(User).where(
        User.email == email
    )

    return db.scalar(stmt)

def get_user(
    db: Session,
    user_id: int
) -> User | None:

    return db.get(
        User,
        user_id
    )


def create_user(
    db: Session,
    user: UserCreate
) -> User:

    db_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(
            user.password
        )
    )

    db.add(db_user)

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="User with this email already exists"
        )

    db.refresh(db_user)
    return db_user

def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session
):
    db_user = db.get(
        User,
        user_id
    )

    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    db_user.name = user.name
    db_user.email = user.email

    db.commit()
    db.refresh(db_user)

    return db_user

def patch_user(
    user_id: int,
    user: UserUpdatePartial,
    db: Session
):
    db_user = db.get(
        User,
        user_id
    )

    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    update_data = user.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)

    return db_user

def delete_user(
    user_id: int,
    db: Session
):
    db_user = db.get(
        User,
        user_id
    )

    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    db.delete(db_user)
    db.commit()

    return {"message": "User deleted"}

def get_users(
        min_age: int | None,
        max_age: int | None,
        name: str | None,
        limit: int,
        offset: int,
        db: Session,
):
    stmt = select(User)

    stmt = stmt.offset(offset).limit(limit)

    if min_age is not None:
        stmt = stmt.where(
            User.age >= min_age
        )

    if max_age is not None:
        stmt = stmt.where(
            User.age <= max_age
        )

    if name is not None:
        stmt = stmt.where(
            User.name.ilike(f"%{name}%")
        )

    users = db.scalars(stmt).all()
    return users
