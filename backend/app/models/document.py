from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, Field
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]

class DocumentDB(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId
    filename: str
    content_type: str
    text_content: str
    subject: Optional[str] = None
    difficulty: Optional[str] = None
    concepts: Optional[list[dict]] = None
    chapters: Optional[list[str]] = None
    metadata: Optional[dict] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class DocumentResponse(BaseModel):
    id: PyObjectId = Field(validation_alias="_id")
    user_id: PyObjectId
    filename: str
    subject: Optional[str] = None
    difficulty: Optional[str] = None
    concepts: Optional[list[dict]] = None
    chapters: Optional[list[str]] = None
    metadata: Optional[dict] = None
    uploaded_at: datetime




    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

