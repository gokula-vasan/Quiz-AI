from typing import TypedDict, List, Dict, Optional, Any

class AgentState(TypedDict):
    user_id: str
    document_id: str
    document_text: str
    concepts: Optional[List[Dict[str, Any]]]
    quiz_title: Optional[str]
    quiz_questions: Optional[List[Dict[str, Any]]]
    user_answers: Optional[List[Dict[str, Any]]]
    score: Optional[int]
    evaluation: Optional[List[Dict[str, Any]]]
    weak_topics: Optional[List[str]]
    strong_topics: Optional[List[str]]
    study_plan: Optional[str]
    progress_logged: Optional[bool]
    difficulty: Optional[str]
    question_count: Optional[int]
    quiz_mode: Optional[str]
    progress_summary: Optional[str]



