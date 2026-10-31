from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)

class UserBase(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    role: str | None = Field(
        default=None,
        max_length=20,
    )


class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        max_length=128
    )


class UserResponse(UserBase):
    id: int


class UserUpdate(UserBase):
    pass


class UserUpdatePartial(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    email: EmailStr | None = None

    role: str | None = Field(
        default=None,
        max_length=20,
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str


