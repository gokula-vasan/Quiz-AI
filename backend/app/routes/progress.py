from fastapi import APIRouter, Depends
from app.database import get_database
from app.auth.dependencies import get_current_user
from datetime import datetime, date, timedelta, timezone

router = APIRouter(prefix="/progress", tags=["progress"])

@router.get("/dashboard")
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    db = get_database()
    user_id = str(current_user["_id"])
    
    # 1. Total documents uploaded
    total_docs = await db.documents.count_documents({"user_id": user_id})
    
    # 2. Total quizzes generated
    total_quizzes = await db.quizzes.count_documents({"user_id": user_id})
    
    # 3. Retrieve all attempts chronologically
    cursor = db.attempts.find({"user_id": user_id}).sort("attempted_at", 1)
    attempts = await cursor.to_list(length=100)
    
    total_attempts = len(attempts)
    
    avg_score = 0
    timeline = []
    
    # Topic performance statistics
    topic_attempts = {}  # {topic: {"correct": 0, "total": 0}}
    
    total_correct = 0
    total_questions = 0
    
    for att in attempts:
        total_correct += att.get("score", 0)
        total_questions += att.get("total_questions", 1)
        
        timeline.append({
            "quiz_id": att.get("quiz_id"),
            "score": att.get("score"),
            "total": att.get("total_questions"),
            "percentage": round((att.get("score", 0) / att.get("total_questions", 1)) * 100, 2) if att.get("total_questions", 0) > 0 else 0,
            "date": (att.get("attempted_at").isoformat() + "Z") if isinstance(att.get("attempted_at"), datetime) else str(att.get("attempted_at"))
        })
        
        # Accumulate correct/total counts per topic/concept
        for eq in att.get("evaluated_questions", []):
            topic = eq.get("topic")
            if not topic or topic.strip() == "":
                topic = "Core Concepts"
            # Truncate overly long text fields to keep clean keywords
            if len(topic) > 40:
                topic = topic[:37] + "..."
            
            if topic not in topic_attempts:
                topic_attempts[topic] = {"correct": 0, "total": 0}
            
            topic_attempts[topic]["total"] += 1
            if eq.get("is_correct", False):
                topic_attempts[topic]["correct"] += 1
                
    # Evaluate strong vs weak topics based on accuracy ratio
    strong_topics = []
    weak_topics = []
    
    for topic, stats in topic_attempts.items():
        if stats["total"] > 0:
            accuracy = stats["correct"] / stats["total"]
            if accuracy >= 0.75:
                strong_topics.append(topic)
            elif accuracy <= 0.50:
                weak_topics.append(topic)
                
    # Fallback to general weak topics list if empty
    if not weak_topics and attempts:
        # Extract from manual weak topics lists in attempts
        all_weaks = []
        for att in attempts:
            all_weaks.extend(att.get("weak_topics", []))
        weak_topics = list(set([w for w in all_weaks if w]))

    # Calculate consecutive day study streak
    streak = 0
    if attempts:
        unique_dates = sorted(list(set([
            att.get("attempted_at").date()
            for att in attempts
            if isinstance(att.get("attempted_at"), datetime)
        ])), reverse=True)
        
        today = date.today()
        # Verify if streak is active (meaning they attempted a quiz today or yesterday)
        if unique_dates and (unique_dates[0] == today or unique_dates[0] == today - timedelta(days=1)):
            streak = 1
            for idx in range(len(unique_dates) - 1):
                if unique_dates[idx] - unique_dates[idx+1] == timedelta(days=1):
                    streak += 1
                else:
                    break
                    
    overall_accuracy = round((total_correct / total_questions) * 100, 2) if total_questions > 0 else 0
    
    return {
        "summary": {
            "total_documents": total_docs,
            "total_quizzes": total_quizzes,
            "total_attempts": total_attempts,
            "overall_accuracy": overall_accuracy,
            "total_correct": total_correct,
            "total_questions": total_questions,
            "study_streak": streak
        },
        "timeline": timeline,
        "strong_topics": strong_topics[:5],
        "weak_topics": weak_topics[:5]
    }

