from pydantic import BaseModel, Field

class TreeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TreeUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TreeResponse(BaseModel):
    id: int
    owner_id: int
    title: str

    model_config = {"from_attributes": True}