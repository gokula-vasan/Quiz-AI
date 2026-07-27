from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_database
from app.auth.dependencies import get_current_user
from app.models.quiz import QuizDB, QuizResponse, QuizAttemptDB, QuizAttemptResponse, QuestionAttempt
from app.agents.orchestrator import quiz_generation_graph, quiz_evaluation_graph
from datetime import datetime
from bson import ObjectId

from pydantic import BaseModel

class QuizPreferenceRequest(BaseModel):
    difficulty: str = "Medium"
    question_count: int = 10
    quiz_mode: str = "theory"  # theory, coding, mixed

router = APIRouter(prefix="/quizzes", tags=["quizzes"])

@router.post("/generate/{document_id}", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def generate_quiz(
    document_id: str,
    pref: QuizPreferenceRequest,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    if not ObjectId.is_valid(document_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format.")
        
    doc = await db.documents.find_one({
        "_id": ObjectId(document_id),
        "user_id": str(current_user["_id"])
    })
    
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
        
    try:
        # Invoke LangGraph Quiz Generation Workflow
        state_input = {
            "user_id": str(current_user["_id"]),
            "document_id": document_id,
            "document_text": doc["text_content"],
            "concepts": None,
            "quiz_title": None,
            "quiz_questions": None,
            "user_answers": None,
            "score": None,
            "evaluation": None,
            "weak_topics": None,
            "study_plan": None,
            "progress_logged": False,
            "difficulty": pref.difficulty,
            "question_count": pref.question_count,
            "quiz_mode": pref.quiz_mode
        }


        
        result_state = await quiz_generation_graph.ainvoke(state_input)
        
        quiz_title = result_state.get("quiz_title") or f"Quiz on {doc['filename']}"
        quiz_questions = result_state.get("quiz_questions") or []
        
        # Save generated quiz to database
        quiz_db = QuizDB(
            user_id=str(current_user["_id"]),
            document_id=document_id,
            title=quiz_title,
            questions=quiz_questions,
            created_at=datetime.utcnow()
        )
        
        quiz_dict = quiz_db.model_dump(by_alias=True)
        if quiz_dict.get("_id") is None:
            quiz_dict.pop("_id", None)
            
        result = await db.quizzes.insert_one(quiz_dict)
        quiz_dict["_id"] = result.inserted_id
        
        return QuizResponse.model_validate(quiz_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )

@router.get("", response_model=list[QuizResponse])
async def list_quizzes(current_user: dict = Depends(get_current_user)):
    db = get_database()
    cursor = db.quizzes.find({"user_id": str(current_user["_id"])}).sort("created_at", -1)
    quizzes = await cursor.to_list(length=100)
    return [QuizResponse.model_validate(q) for q in quizzes]

@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(quiz_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    if not ObjectId.is_valid(quiz_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid quiz ID format.")
        
    quiz = await db.quizzes.find_one({
        "_id": ObjectId(quiz_id),
        "user_id": str(current_user["_id"])
    })
    
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")
        
    return QuizResponse.model_validate(quiz)

@router.post("/submit/{quiz_id}", response_model=QuizAttemptResponse, status_code=status.HTTP_201_CREATED)
async def submit_quiz(
    quiz_id: str,
    answers: list[QuestionAttempt],
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    if not ObjectId.is_valid(quiz_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid quiz ID format.")
        
    quiz = await db.quizzes.find_one({
        "_id": ObjectId(quiz_id),
        "user_id": str(current_user["_id"])
    })
    
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")
        
    try:
        user_answers_dict = [ans.model_dump() for ans in answers]
        
        # Invoke LangGraph Quiz Evaluation Workflow
        state_input = {
            "user_id": str(current_user["_id"]),
            "document_id": quiz["document_id"],
            "document_text": "",
            "concepts": None,
            "quiz_title": quiz["title"],
            "quiz_questions": quiz["questions"],
            "user_answers": user_answers_dict,
            "score": None,
            "evaluation": None,
            "weak_topics": None,
            "study_plan": None,
            "progress_logged": False
        }
        
        result_state = await quiz_evaluation_graph.ainvoke(state_input)
        
        score = result_state.get("score") or 0
        evaluation = result_state.get("evaluation") or []
        weak_topics = result_state.get("weak_topics") or []
        study_plan = result_state.get("study_plan")
        progress_summary = result_state.get("progress_summary")
        
        # Save quiz attempt details to database
        percentage = round((score / len(quiz["questions"])) * 100, 2) if quiz["questions"] else 0.0
        attempt_db = QuizAttemptDB(
            quiz_id=quiz_id,
            user_id=str(current_user["_id"]),
            answers=answers,
            score=score,
            total_questions=len(quiz["questions"]),
            percentage=percentage,
            evaluated_questions=evaluation,
            weak_topics=weak_topics,
            study_plan=study_plan,
            progress_summary=progress_summary,
            attempted_at=datetime.utcnow()
        )
        
        attempt_dict = attempt_db.model_dump(by_alias=True)
        if attempt_dict.get("_id") is None:
            attempt_dict.pop("_id", None)
            
        result = await db.attempts.insert_one(attempt_dict)
        attempt_dict["_id"] = result.inserted_id
        
        return QuizAttemptResponse.model_validate(attempt_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit and evaluate quiz: {str(e)}"
        )

@router.get("/attempts/history", response_model=list[QuizAttemptResponse])
async def get_attempts_history(current_user: dict = Depends(get_current_user)):
    db = get_database()
    cursor = db.attempts.find({"user_id": str(current_user["_id"])}).sort("attempted_at", -1)
    attempts = await cursor.to_list(length=100)
    return [QuizAttemptResponse.model_validate(att) for att in attempts]
