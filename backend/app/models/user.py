from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, Field, EmailStr
from datetime import datetime

# Custom type for handling MongoDB ObjectId validation in Pydantic v2
PyObjectId = Annotated[str, BeforeValidator(str)]

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: PyObjectId = Field(validation_alias="_id")
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class UserInDB(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    email: EmailStr
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
