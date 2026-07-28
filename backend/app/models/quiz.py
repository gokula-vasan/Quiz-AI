from typing import Annotated, Optional, List, Dict
from pydantic import BaseModel, BeforeValidator, Field
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]

class QuizQuestion(BaseModel):
    id: str
    type: str = "mcq"  # mcq, true_false, fill_in_the_blank, short_answer, coding
    question_text: str
    options: Optional[List[str]] = None  # Populated for mcq and true_false
    correct_option: Optional[int] = None  # Populated for mcq and true_false (0-indexed)
    correct_answer: Optional[str] = None  # Populated for fill_in_the_blank, short_answer, coding
    code_template: Optional[str] = None  # Starter template for coding questions
    explanation: str
    topic: Optional[str] = None
    chapter: Optional[str] = None
    difficulty: Optional[str] = None

class QuizDB(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId
    document_id: PyObjectId
    title: str
    questions: List[QuizQuestion]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class QuizResponse(BaseModel):
    id: PyObjectId = Field(validation_alias="_id")
    user_id: PyObjectId
    document_id: PyObjectId
    title: str
    questions: List[QuizQuestion]
    created_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class QuestionAttempt(BaseModel):
    question_id: str
    selected_option: Optional[int] = -1
    text_response: Optional[str] = None


class QuizAttemptDB(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    quiz_id: PyObjectId
    user_id: PyObjectId
    answers: List[QuestionAttempt]
    score: int
    total_questions: int
    percentage: float
    evaluated_questions: List[dict]  # Contains question details, selected vs correct option, explanation
    weak_topics: List[str]
    strong_topics: List[str] = Field(default_factory=list)
    study_plan: Optional[str] = None
    progress_summary: Optional[str] = None
    attempted_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class QuizAttemptResponse(BaseModel):
    id: PyObjectId = Field(validation_alias="_id")
    quiz_id: PyObjectId
    user_id: PyObjectId
    score: int
    total_questions: int
    percentage: float
    evaluated_questions: List[dict]
    weak_topics: List[str]
    strong_topics: List[str] = Field(default_factory=list)
    study_plan: Optional[str] = None
    progress_summary: Optional[str] = None
    attempted_at: datetime



    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
