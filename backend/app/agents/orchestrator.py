import json
import logging
import re
from typing import List, Dict, Any
from pydantic import BaseModel
from google import genai
from google.genai import types
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.config import GEMINI_API_KEY


logger = logging.getLogger("uvicorn.error")

from bson import ObjectId
from app.database import get_database

import random

# ================= Analysis Schemas =================

class ConceptItem(BaseModel):
    topic: str
    chapter: str  # The chapter or section this topic belongs to
    summary: str
    key_points: List[str]
    difficulty: str  # Easy, Medium, Hard

class AnalysisResponse(BaseModel):
    subject: str
    overall_difficulty: str
    chapters: List[str]  # Detected chapters/sections
    concepts: List[ConceptItem]
    metadata: Dict[str, str]  # Structured study metadata (e.g. key terms, estimated study time)

# ================= Local Fallback Extractor =================

# ================= Local Fallback Extractor Helpers =================

def is_valid_study_paragraph(p: str) -> bool:
    """
    Filters out academic paper headers, emails, citations, and author lists.
    """
    p_lower = p.lower()
    
    # 1. Exclude emails
    if "@" in p or "mailto:" in p:
        return False
        
    # 2. Exclude affiliations, citations, and header metadata
    exclusions = [
        "department of", "university", "institute of", "college", "school of",
        "cite this", "citation", "doi:", "https://", "http://", "www.",
        "abstract", "keywords:", "accepted:", "received:", "published online",
        "volume ", "issue ", "page ", "journal of", "proceedings of",
        "editor-in-chief", "copyright", "all rights reserved"
    ]
    for exc in exclusions:
        if exc in p_lower:
            return False
            
    # 3. Exclude author list patterns (e.g. lists of initials and names with multiple semicolons)
    if p.count(";") > 2 or p.count(",") > 5:
        words = p.split()
        if len(words) < 15:
            return False
            
    # 4. Require a minimum word count to be a meaningful conceptual definition
    if len(p.split()) < 10:
        return False
        
    return True

def get_fallback_concepts(text: str) -> dict:
    """
    Local fallback parser to generate key topics if Gemini API is not configured or fails.
    Ensures exactly 10 concepts are returned to generate exactly 10 questions.
    """
    # Replace newlines with spaces to merge line wraps, and clean extra whitespace
    single_line_text = re.sub(r'\s+', ' ', text.replace("\n", " "))
    
    # Split by periods to get grammatically complete sentences instead of line fragments
    sentences = [s.strip() for s in single_line_text.split(".") if s.strip()]
    
    # Filter lines to only include actual content paragraphs
    study_paragraphs = [p for p in sentences if is_valid_study_paragraph(p)]
    
    # If we filtered everything, relax constraints to prevent crash
    if not study_paragraphs:
        study_paragraphs = [p for p in sentences if len(p.split()) > 5]
        
    concepts = []
    chapters = ["Chapter 1: Basics", "Chapter 2: Core Analysis", "Chapter 3: Advanced Concepts"]
    
    limit = min(len(study_paragraphs), 10)
    for i in range(limit):
        paragraph = study_paragraphs[i]
        
        # Clean starting filler words from topic names
        topic_text = paragraph
        filler_prefixes = ["in this paper,", "we propose", "we present", "this section", "firstly,", "secondly,", "our results"]
        for prefix in filler_prefixes:
            if topic_text.lower().startswith(prefix):
                topic_text = topic_text[len(prefix):].strip()
                
        words = topic_text.split()
        topic = " ".join(words[:4]).replace(".", "").replace(",", "").replace(":", "").strip()
        
        # Clean trailing prepositions and small words from fallback topics
        stop_words = ["to", "or", "and", "the", "a", "an", "of", "in", "by", "for", "with", "as", "is", "are", "than", "from"]
        topic_words = topic.split()
        while topic_words and topic_words[-1].lower() in stop_words:
            topic_words.pop()
        topic = " ".join(topic_words)
        
        if not topic or len(topic) < 3:
            topic = f"Key Concept Topic {i+1}"
            
        chapter_index = min(i // 4, len(chapters) - 1)
        concepts.append({
            "topic": topic,
            "chapter": chapters[chapter_index],
            "summary": paragraph[:250] + "..." if len(paragraph) > 250 else paragraph,
            "key_points": [
                paragraph[:100] + "..." if len(paragraph) > 100 else paragraph,
                "Essential study concept detail."
            ],
            "difficulty": "Easy" if i < 3 else ("Medium" if i < 7 else "Hard")
        })
        
    # Pad to ensure we have exactly 10 concepts so we can generate exactly 10 questions
    while len(concepts) < 10:
        idx = len(concepts)
        concepts.append({
            "topic": f"Core Concept Definition {idx + 1}",
            "chapter": "Chapter 3: Advanced Concepts",
            "summary": f"This section covers key terms and autonomous testing requirements for concept review {idx + 1}.",
            "key_points": ["Study material analysis verification.", "Autonomous agent quiz preparation."],
            "difficulty": "Hard"
        })
        
    return {
        "chapters": chapters,
        "concepts": concepts,
        "metadata": {
            "estimated_study_time": "30 minutes",
            "key_terms": "Autonomous learning, Practice quiz, Concept review",
            "target_audience": "Exam Prep Student"
        }
    }



from typing import List, Dict, Any, Optional

logger = logging.getLogger("uvicorn.error")

from bson import ObjectId
from app.database import get_database

import random

# ================= Analysis Schemas =================

class ConceptItem(BaseModel):
    topic: str
    chapter: str  # The chapter or section this topic belongs to
    summary: str
    key_points: List[str]
    difficulty: str  # Easy, Medium, Hard

class AnalysisResponse(BaseModel):
    subject: str
    overall_difficulty: str
    chapters: List[str]  # Detected chapters/sections
    concepts: List[ConceptItem]
    metadata: Dict[str, str]  # Structured study metadata (e.g. key terms, estimated study time)

# ================= Local Fallback Extractor Helpers =================

def is_valid_study_paragraph(p: str) -> bool:
    """
    Filters out academic paper headers, emails, citations, and author lists.
    """
    p_lower = p.lower()
    
    # 1. Exclude emails
    if "@" in p or "mailto:" in p:
        return False
        
    # 2. Exclude affiliations, citations, and header metadata
    exclusions = [
        "department of", "university", "institute of", "college", "school of",
        "cite this", "citation", "doi:", "https://", "http://", "www.",
        "abstract", "keywords:", "accepted:", "received:", "published online",
        "volume ", "issue ", "page ", "journal of", "proceedings of",
        "editor-in-chief", "copyright", "all rights reserved"
    ]
    for exc in exclusions:
        if exc in p_lower:
            return False
            
    # 3. Exclude author list patterns (e.g. lists of initials and names with multiple semicolons)
    if p.count(";") > 2 or p.count(",") > 5:
        words = p.split()
        if len(words) < 15:
            return False
            
    # 4. Require a minimum word count to be a meaningful conceptual definition
    if len(p.split()) < 10:
        return False
        
    return True

def get_fallback_concepts(text: str) -> dict:
    """
    Local fallback parser to generate key topics if Gemini API is not configured or fails.
    Ensures exactly 10 concepts are returned to generate exactly 10 questions.
    """
    # Replace newlines with spaces to merge line wraps, and clean extra whitespace
    single_line_text = re.sub(r'\s+', ' ', text.replace("\n", " "))
    
    # Split by periods to get grammatically complete sentences instead of line fragments
    sentences = [s.strip() for s in single_line_text.split(".") if s.strip()]
    
    # Filter lines to only include actual content paragraphs
    study_paragraphs = [p for p in sentences if is_valid_study_paragraph(p)]
    
    # If we filtered everything, relax constraints to prevent crash
    if not study_paragraphs:
        study_paragraphs = [p for p in sentences if len(p.split()) > 5]
        
    concepts = []
    chapters = ["Chapter 1: Basics", "Chapter 2: Core Analysis", "Chapter 3: Advanced Concepts"]
    
    limit = min(len(study_paragraphs), 10)
    for i in range(limit):
        paragraph = study_paragraphs[i]
        
        # Clean starting filler words from topic names
        topic_text = paragraph.strip()
        filler_prefixes = [
            "in this paper,", "we propose", "we present", "this section", 
            "firstly,", "secondly,", "our results", "regarding", 
            "when studying", "write a", "implement", "true or false:", 
            "what is the", "what are", "explanation of", "understanding"
        ]
        
        # Keep stripping prefixes case-insensitively
        stripped = True
        while stripped:
            stripped = False
            for prefix in filler_prefixes:
                if topic_text.lower().startswith(prefix):
                    topic_text = topic_text[len(prefix):].strip()
                    stripped = True
                    break
                    
        words = topic_text.split()
        topic = " ".join(words[:3]).replace(".", "").replace(",", "").replace(":", "").replace("'", "").replace("\"", "").strip()
        
        # Clean trailing prepositions and small words from fallback topics
        stop_words = ["to", "or", "and", "the", "a", "an", "of", "in", "by", "for", "with", "as", "is", "are", "than", "from"]
        topic_words = topic.split()
        while topic_words and topic_words[-1].lower() in stop_words:
            topic_words.pop()
        topic = " ".join(topic_words)
        
        if not topic or len(topic) < 3:
            topic = f"Key Concept Topic {i+1}"
            
        chapter_index = min(i // 4, len(chapters) - 1)
        concepts.append({
            "topic": topic,
            "chapter": chapters[chapter_index],
            "summary": paragraph[:250] + "..." if len(paragraph) > 250 else paragraph,
            "key_points": [
                paragraph[:100] + "..." if len(paragraph) > 100 else paragraph,
                "Essential study concept detail."
            ],
            "difficulty": "Easy" if i < 3 else ("Medium" if i < 7 else "Hard")
        })
        
    # Pad to ensure we have exactly 10 concepts so we can generate exactly 10 questions
    while len(concepts) < 10:
        idx = len(concepts)
        concepts.append({
            "topic": f"Core Concept Definition {idx + 1}",
            "chapter": "Chapter 3: Advanced Concepts",
            "summary": f"This section covers key terms and autonomous testing requirements for concept review {idx + 1}.",
            "key_points": ["Study material analysis verification.", "Autonomous agent quiz preparation."],
            "difficulty": "Hard"
        })
        
    return {
        "chapters": chapters,
        "concepts": concepts,
        "metadata": {
            "estimated_study_time": "30 minutes",
            "key_terms": "Autonomous learning, Practice quiz, Concept review",
            "target_audience": "Exam Prep Student"
        }
    }

async def save_analysis_to_db(doc_id: str, subject: str, difficulty: str, concepts: list, chapters: list, metadata: dict):
    """
    Helper to store analyzed subject, difficulty, chapters, concepts, and metadata in MongoDB.
    """
    try:
        db = get_database()
        if doc_id and ObjectId.is_valid(doc_id):
            await db.documents.update_one(
                {"_id": ObjectId(doc_id)},
                {"$set": {
                    "subject": subject,
                    "difficulty": difficulty,
                    "concepts": concepts,
                    "chapters": chapters,
                    "metadata": metadata
                }}
            )
            logger.info(f"Content Analysis Agent: Updated MongoDB document '{doc_id}' with subject: '{subject}', chapters: {len(chapters)}")
    except Exception as e:
        logger.error(f"Failed to save content analysis to database: {e}")

# ================= Quiz Generation Schemas =================

class QuestionSchema(BaseModel):
    id: str  # q1, q2, ...
    type: str  # mcq, true_false, fill_in_the_blank, short_answer, coding
    question_text: str
    options: Optional[List[str]] = None
    correct_option: Optional[int] = None
    correct_answer: Optional[str] = None
    code_template: Optional[str] = None
    explanation: str
    topic: Optional[str] = None
    chapter: Optional[str] = None
    difficulty: Optional[str] = None


class QuizGenerationResponse(BaseModel):
    quiz_title: str
    quiz_questions: List[QuestionSchema]

# ================= Quiz Evaluation Schemas =================

class EvaluatedQuestionSchema(BaseModel):
    question_id: str
    question_text: str
    selected_option: Optional[int] = -1
    text_response: Optional[str] = None
    is_correct: bool
    explanation: str
    topic: Optional[str] = None
    chapter: Optional[str] = None

class EvaluationResponse(BaseModel):
    score: int
    evaluated_questions: List[EvaluatedQuestionSchema]
    weak_topics: List[str]
    strong_topics: List[str]

# ================= Local Fallback Quiz Generator =================

def get_fallback_quiz(concepts: list, question_count: int = 10, quiz_mode: str = "theory") -> dict:
    """
    Generates a mock quiz locally based on concepts if the Gemini API fails or is not set up.
    Creates question_count distinct questions matching standard course topics, cycling through styles matching quiz_mode.
    """
    questions = []
    padded_concepts = list(concepts)
    while len(padded_concepts) < question_count:
        idx = len(padded_concepts)
        if concepts:
            # Cycle through existing concepts to preserve selected topic
            padded_concepts.append(concepts[idx % len(concepts)])
        else:
            padded_concepts.append({
                "topic": f"Term Definition {idx+1}",
                "summary": "Covers general review and study material parameters.",
                "key_points": ["Study material analysis metrics."],
                "difficulty": "Medium",
                "chapter": "Core Concepts"
            })
        
    for idx in range(question_count):
        current = padded_concepts[idx]
        correct_topic = current.get("topic", "Topic")
        description = current.get("summary", "Topic description.")
        chapter = current.get("chapter", "Core Concepts")
        q_id = f"q{idx+1}"
        
        # Select question types based on quiz_mode
        if quiz_mode == "theory":
            theory_types = ["mcq", "true_false", "fill_in_the_blank", "short_answer"]
            q_type = theory_types[idx % len(theory_types)]
        elif quiz_mode == "coding":
            q_type = "coding"
        else: # mixed
            mixed_types = ["mcq", "true_false", "fill_in_the_blank", "short_answer", "coding"]
            q_type = mixed_types[idx % len(mixed_types)]
            
        short_desc = description[:140] + "..." if len(description) > 140 else description
        
        if q_type == "mcq":
            incorrect_pool = [c.get("topic", "") for i, c in enumerate(padded_concepts) if i != idx and c.get("topic", "")]
            incorrect_pool = list(set([x for x in incorrect_pool if x]))
            while len(incorrect_pool) < 3:
                incorrect_pool.append(f"Review Concept {len(incorrect_pool)+1}")
            wrong_choices = incorrect_pool[:3]
            options = [correct_topic] + wrong_choices
            correct_index = random.randint(0, 3)
            options[0], options[correct_index] = options[correct_index], options[0]
            
            questions.append({
                "id": q_id,
                "type": "mcq",
                "question_text": f"Which concept matches the following description: '{short_desc}'?",
                "options": options,
                "correct_option": correct_index,
                "explanation": f"The term '{correct_topic}' is defined as: {description}",
                "topic": correct_topic,
                "chapter": chapter,
                "difficulty": current.get("difficulty", "Medium")
            })
            
        elif q_type == "true_false":
            correct_val = random.choice([True, False])
            correct_option = 0 if correct_val else 1
            stmt = description if correct_val else f"It is widely accepted that '{correct_topic}' has no practical application in learning modules."
            
            questions.append({
                "id": q_id,
                "type": "true_false",
                "question_text": f"True or False: {stmt}",
                "options": ["True", "False"],
                "correct_option": correct_option,
                "explanation": f"This statement is {'correct' if correct_val else 'incorrect'} based on the topic '{correct_topic}'.",
                "topic": correct_topic,
                "chapter": chapter,
                "difficulty": current.get("difficulty", "Medium")
            })
            
        elif q_type == "fill_in_the_blank":
            words = correct_topic.split()
            blank_word = words[-1] if words else "concept"
            sentence = f"The term '{correct_topic.replace(blank_word, '_______')}' represents the concept defined by: {short_desc}"
            
            questions.append({
                "id": q_id,
                "type": "fill_in_the_blank",
                "question_text": sentence,
                "correct_answer": blank_word,
                "explanation": f"The blank word is '{blank_word}', completing the concept for '{correct_topic}'.",
                "topic": correct_topic,
                "chapter": chapter,
                "difficulty": current.get("difficulty", "Medium")
            })
            
        elif q_type == "short_answer":
            questions.append({
                "id": q_id,
                "type": "short_answer",
                "question_text": f"In your own words, briefly explain the core utility and main purpose of '{correct_topic}'?",
                "correct_answer": description,
                "explanation": f"A standard answer should mention: {description}",
                "topic": correct_topic,
                "chapter": chapter,
                "difficulty": current.get("difficulty", "Medium")
            })
            
        elif q_type == "coding":
            questions.append({
                "id": q_id,
                "type": "coding",
                "question_text": f"Write a Python helper function structure to model or check '{correct_topic}' parameter parameters.",
                "code_template": f"def test_{correct_topic.lower().replace(' ', '_')}(data):\n    # Write logic to review '{correct_topic}'\n    return True\n",
                "correct_answer": "Should return boolean flag representing validation check.",
                "explanation": f"This skeleton models basic logic processing validations for {correct_topic} parameters.",
                "topic": correct_topic,
                "chapter": chapter,
                "difficulty": current.get("difficulty", "Medium")
            })
            
    return {
        "quiz_title": "Comprehensive Dynamic Practice Quiz",
        "quiz_questions": questions
    }

# ================= Local Fallback Quiz Evaluator =================

def local_evaluate_quiz(questions: list, answers: list) -> dict:
    """
    Locally grades student attempts in offline mode, accommodating written responses.
    """
    score = 0
    evaluated = []
    
    # Track correct / total per topic/chapter
    topic_scores = {} # {topic: {"correct": 0, "total": 0}}
    
    for q in questions:
        q_id = q.get("id")
        q_type = q.get("type", "mcq")
        q_text = q.get("question_text", "")
        explanation = q.get("explanation", "")
        topic = q.get("topic") or "General Core"
        chapter = q.get("chapter") or "Core Concepts"
        
        if topic not in topic_scores:
            topic_scores[topic] = {"correct": 0, "total": 0}
        topic_scores[topic]["total"] += 1
        
        ans = next((a for a in answers if a.get("question_id") == q_id), None)
        selected = ans.get("selected_option") if ans else -1
        text_resp = ans.get("text_response") if ans else ""
        
        is_correct = False
        
        if q_type in ("mcq", "true_false"):
            is_correct = (selected == q.get("correct_option"))
        elif q_type == "fill_in_the_blank":
            ref = q.get("correct_answer") or ""
            is_correct = (text_resp.strip().lower() == ref.strip().lower()) if text_resp else False
        else:  # short_answer, coding
            is_correct = len(text_resp.strip()) > 5 if text_resp else False
            if not is_correct:
                explanation = "Your answer was empty or too brief. Try to explain in more detail!"
                
        if is_correct:
            score += 1
            topic_scores[topic]["correct"] += 1
            
        evaluated.append({
            "question_id": q_id,
            "question_text": q_text,
            "selected_option": selected,
            "text_response": text_resp,
            "is_correct": is_correct,
            "explanation": explanation,
            "topic": topic,
            "chapter": chapter
        })
        
    strong_topics = []
    weak_topics = []
    for topic, stats in topic_scores.items():
        accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        if accuracy >= 0.75:
            strong_topics.append(topic)
        else:
            weak_topics.append(topic)
            
    return {
        "score": score,
        "evaluated_questions": evaluated,
        "weak_topics": weak_topics,
        "strong_topics": strong_topics
    }

# ================= Node Definitions =================

async def analyze_content_node(state: AgentState) -> dict:
    logger.info("Content Analysis Agent: Running...")
    concepts = state.get("concepts")
    if concepts:
        logger.info("Content Analysis Agent: Concepts already present in state. Skipping generation.")
        return {"concepts": concepts}
        
    text = state.get("document_text", "")
    doc_id = state.get("document_id", "")
    if not text:
        logger.warning("No document text provided for analysis.")
        return {"concepts": []}
        
    # Check if Gemini key is set to a placeholder
    api_key = GEMINI_API_KEY or ""
    is_placeholder = any(x in api_key.lower() for x in ["placeholder", "your_actual", "here"]) or not api_key.strip()
    
    if is_placeholder:
        logger.warning("GEMINI_API_KEY is not configured. Running local fallback analysis.")
        fallback_data = get_fallback_concepts(text)
        concepts = fallback_data.get("concepts", [])
        chapters = fallback_data.get("chapters", [])
        metadata = fallback_data.get("metadata", {})
        await save_analysis_to_db(doc_id, "General Study Notes", "Medium", concepts, chapters, metadata)
        return {"concepts": concepts}
        
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        You are the Content Analysis Agent in the QuizMaster AI platform. 
        Your task is to analyze the following study material text, understand its core subject,
        and extract the key chapters, topics, subtopics, and metadata.
        
        For each concept, provide:
        - A clear topic/concept name.
        - The chapter or section name it belongs to.
        - A concise summary of the concept.
        - 2 to 4 key points/details explaining the concept.
        - The relative difficulty of the concept (Easy, Medium, Hard).
        
        Also identify the general subject, detected chapters/sections list, overall difficulty,
        and study metadata including key terms and estimated study time.
        
        Study Material Text:
        {text}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AnalysisResponse,
                temperature=0.15
            )
        )
        
        analysis_data = json.loads(response.text)
        concepts = analysis_data.get("concepts", [])
        subject = analysis_data.get("subject") or "General Study Notes"
        overall_difficulty = analysis_data.get("overall_difficulty") or "Medium"
        chapters = analysis_data.get("chapters") or ["General Core"]
        metadata = analysis_data.get("metadata") or {}
        
        await save_analysis_to_db(doc_id, subject, overall_difficulty, concepts, chapters, metadata)
        logger.info(f"Content Analysis Agent: Successfully analyzed content and extracted {len(concepts)} concepts.")
        return {"concepts": concepts}
        
    except Exception as e:
        logger.error(f"Error in Content Analysis Agent: {e}. Falling back to local extractor.")
        fallback_data = get_fallback_concepts(text)
        concepts = fallback_data.get("concepts", [])
        chapters = fallback_data.get("chapters", [])
        metadata = fallback_data.get("metadata", {})
        await save_analysis_to_db(doc_id, "General Study Notes", "Medium", concepts, chapters, metadata)
        return {"concepts": concepts}



async def generate_quiz_node(state: AgentState) -> dict:
    logger.info("Quiz Generation Agent: Running...")
    concepts = state.get("concepts", [])
    if not concepts:
        logger.warning("No concepts provided for quiz generation.")
        return {"quiz_title": "Concept Practice Quiz", "quiz_questions": []}
        
    api_key = GEMINI_API_KEY or ""
    is_placeholder = any(x in api_key.lower() for x in ["placeholder", "your_actual", "here"]) or not api_key.strip()
    
    difficulty = state.get("difficulty", "Medium")
    question_count = state.get("question_count", 10)
    quiz_mode = state.get("quiz_mode", "theory")
    
    if is_placeholder:
        logger.warning("GEMINI_API_KEY is not configured. Running local fallback quiz generation.")
        return get_fallback_quiz(concepts, question_count, quiz_mode)
        
    try:
        client = genai.Client(api_key=api_key)
        concepts_formatted = json.dumps(concepts, indent=2)
        
        # Configure format guidelines prompt text based on quiz_mode
        if quiz_mode == "theory":
            format_instructions = """
            - DO NOT generate any coding or programming questions.
            - Generate only conceptual/theory questions: Multiple Choice Questions (MCQ), True/False Questions, Fill in the Blanks, and Short Answer Questions.
            - MCQ Options must be very short and concise (typically 1 to 5 words maximum).
            """
        elif quiz_mode == "coding":
            format_instructions = """
            - Generate ONLY coding/programming questions.
            - Provide a Python code starter template in code_template and the target explanation/criteria in correct_answer.
            """
        else: # mixed
            format_instructions = """
            - Provide a diverse mix of both theory questions (MCQ, True/False, Fill in the Blanks, Short Answers) and coding questions.
            - MCQ Options must be very short and concise (typically 1 to 5 words maximum).
            """
        
        prompt = f"""
        You are the Quiz Generation Agent in the QuizMaster AI platform.
        Your persona: You are an expert university professor, competitive programming instructor, and technical interviewer.
        
        Your task is to generate a personalized HIGH-QUALITY quiz based on the key concepts extracted ONLY from the uploaded study material.
        
        The student has requested:
        - Target Difficulty Level: {difficulty}
        - Total Questions Requested: {question_count}
        - Quiz Mode: {quiz_mode.upper()}
        
        STRICT RULES:
        1. Read and understand the entire document/concepts before generating questions.
        2. Extract only the important topics, subtopics, concepts, formulas, definitions, algorithms, and examples from the uploaded document.
        3. Generate questions ONLY from the uploaded document. Do NOT use outside topics.
        4. Every question must test conceptual understanding instead of simple memorization.
        5. Never repeat the same concept in different wording.
        6. Every question must be unique. Avoid duplicate or ambiguous questions.
        7. Every Multiple Choice Question (MCQ) must contain exactly FOUR options.
        8. Only ONE option must be correct. The remaining three options must be realistic distractors that belong to the same topic and look believable (e.g. stack, queue, priority queue, deque instead of stack, apple, elephant, car).
        9. Randomize the position of the correct answer index (do not always keep it as option B or C).
        10. Target Difficulty Distribution:
            - 30% Easy questions
            - 50% Medium questions
            - 20% Hard questions
        11. Format guidelines based on the current Quiz Mode ({quiz_mode.upper()}):
            {format_instructions}
            
            Aim for a diverse mix of cognitive levels from Bloom's Taxonomy (Remember, Understand, Apply, Analyze, Evaluate, Create) including:
            - Conceptual MCQs (40%)
            - Scenario-based MCQs (20%) (e.g. "You are developing a browser's Back button. Which data structure should you use?")
            - Application-based Questions (15%) (e.g. "You need to search one million sorted records quickly. Which algorithm is the most suitable?")
            - Coding challenges (15%) (e.g. "Write a function to reverse a linked list")
            - True/False or Fill in the Blank concepts (10%)
        12. For every question, you MUST populate: question_text, options, correct_option, correct_answer, explanation, topic, chapter, and difficulty.
            The `topic` field MUST be exactly one of the topic names listed in the "Key Concepts" below (e.g. if the concept topic is "Data Structures", the question's topic MUST be "Data Structures"). Do NOT make up new topic names, do NOT use question text, templates, or descriptions as the topic name.
        13. The explanation should clearly explain WHY the correct option/answer is correct and WHY the others are incorrect.
        14. If the uploaded document has code snippets, formulas, tables, or diagrams, generate questions from them whenever possible.
        15. If the uploaded document does not contain enough information, do NOT invent questions. Generate questions only from the available content.
        16. Ensure the quiz is suitable for university-level students and technical interview preparation.
        
        Strictly format the JSON output using the QuizGenerationResponse schema.
        
        Key Concepts:
        {concepts_formatted}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=QuizGenerationResponse,
                temperature=0.25
            )
        )
        
        quiz_data = json.loads(response.text)
        questions = quiz_data.get("quiz_questions", [])
        title = quiz_data.get("quiz_title") or "Concept Practice Quiz"
        logger.info(f"Quiz Generation Agent: Successfully generated quiz '{title}' with {len(questions)} questions.")
        return {
            "quiz_title": title,
            "quiz_questions": questions
        }
        
    except Exception as e:
        logger.error(f"Error in Quiz Generation Agent: {e}. Falling back to local quiz generator.")
        return get_fallback_quiz(concepts, question_count, quiz_mode)






async def evaluate_answers_node(state: AgentState) -> dict:
    logger.info("Evaluation Agent: Running...")
    questions = state.get("quiz_questions", [])
    answers = state.get("user_answers", [])
    
    api_key = GEMINI_API_KEY or ""
    is_placeholder = any(x in api_key.lower() for x in ["placeholder", "your_actual", "here"]) or not api_key.strip()
    
    if is_placeholder:
        logger.warning("GEMINI_API_KEY is not configured. Running local fallback evaluation.")
        eval_data = local_evaluate_quiz(questions, answers)
        return {
            "score": eval_data["score"],
            "evaluation": eval_data["evaluated_questions"],
            "weak_topics": eval_data["weak_topics"],
            "strong_topics": eval_data["strong_topics"]
        }
        
    try:
        client = genai.Client(api_key=api_key)
        
        payload = {
            "questions": questions,
            "answers": answers
        }
        
        prompt = f"""
        You are the Evaluation Agent in the QuizMaster AI platform.
        Your task is to grade the student's quiz submissions.
        
        Evaluate each question:
        - MCQ / True-False: Compare selected_option index with correct_option index.
        - Fill in the Blanks: Check if text_response matches correct_answer (allow minor case/spacing variations).
        - Short Answer / Coding: Review text_response qualitatively against correct_answer reference parameters and logic. If correct, mark is_correct=true.
        
        For each evaluated question, copy its corresponding `topic` and `chapter` from the input questions payload.
        
        Provide the score, evaluated questions list with personalized explanation feedback for why their answer is correct/incorrect, list of weak topics (accuracy < 75%), and list of strong topics (accuracy >= 75%).
        
        Quiz Details:
        {json.dumps(payload, indent=2)}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EvaluationResponse,
                temperature=0.1
            )
        )
        
        eval_data = json.loads(response.text)
        evaluated = eval_data.get("evaluated_questions") or []
        
        # Programmatically map and ensure topic and chapter are copied from the original quiz questions list
        for eq in evaluated:
            q_id = eq.get("question_id")
            original_q = next((q for q in questions if q.get("id") == q_id), None)
            if original_q:
                eq["topic"] = original_q.get("topic") or eq.get("topic") or "General Concept"
                eq["chapter"] = original_q.get("chapter") or eq.get("chapter") or "Core Chapter"
                
        # Re-verify strong vs weak topics based on programmatic mapping correctness
        topic_scores = {}
        for eq in evaluated:
            topic = eq.get("topic") or "General Concept"
            if topic not in topic_scores:
                topic_scores[topic] = {"correct": 0, "total": 0}
            topic_scores[topic]["total"] += 1
            if eq.get("is_correct", False):
                topic_scores[topic]["correct"] += 1
                
        strong_topics = []
        weak_topics = []
        for topic, stats in topic_scores.items():
            accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            if accuracy >= 0.75:
                strong_topics.append(topic)
            else:
                weak_topics.append(topic)

        logger.info(f"Evaluation Agent: Successfully graded attempt. Score: {eval_data.get('score')}/10")
        return {
            "score": eval_data.get("score") or 0,
            "evaluation": evaluated,
            "weak_topics": weak_topics,
            "strong_topics": strong_topics
        }
        
    except Exception as e:
        logger.error(f"Error in Evaluation Agent: {e}. Falling back to local evaluator.")
        eval_data = local_evaluate_quiz(questions, answers)
        return {
            "score": eval_data["score"],
            "evaluation": eval_data["evaluated_questions"],
            "weak_topics": eval_data["weak_topics"],
            "strong_topics": eval_data["strong_topics"]
        }

def get_fallback_study_plan(score: int, total: int, weak_topics: list, strong_topics: list, history: str) -> str:
    """
    Generates a structured, encouraging fallback study plan locally.
    """
    accuracy = int(round((score / total) * 100)) if total else 0
    past_info = f"\n*Status Update*: {history}\n" if history else ""
    
    # Calculate estimated study time: 30 minutes per weak topic, at least 30 minutes if any
    weak_count = len(weak_topics)
    est_minutes = max(30, weak_count * 30) if weak_count > 0 else 0
    est_hours_str = f"{est_minutes // 60} Hours {est_minutes % 60} Minutes" if est_minutes >= 60 else f"{est_minutes} Minutes"
    if est_minutes == 0:
        est_hours_str = "0 minutes (Perfect score!)"
        
    # Formulate numbered study plan steps
    plan_steps = []
    if weak_topics:
        step_num = 1
        for topic in weak_topics:
            plan_steps.append(f"{step_num}. Revise {topic} Core Concepts (30 minutes)")
            step_num += 1
            plan_steps.append(f"{step_num}. Practice 10-15 MCQs on {topic}")
            step_num += 1
        plan_steps.append(f"{step_num}. Take a follow-up Quiz on these weak areas tomorrow.")
    else:
        plan_steps.append("1. Outstanding work! You have mastered all concepts.")
        plan_steps.append("2. Challenge yourself by changing the quiz difficulty to Hard.")
        plan_steps.append("3. Try out the Coding Mode for hands-on programming challenges.")
        
    steps_formatted = "\n".join([f"{step}" for step in plan_steps])
    
    strong_list = ", ".join(strong_topics) if strong_topics else "None yet"
    weak_list = ", ".join(weak_topics) if weak_topics else "None"
    
    return f"""### 📚 Personalized Study Plan
{steps_formatted}

### ⏱️ Estimated Study Time
* **Total Duration**: {est_hours_str}

### 📊 Performance Summary & Learning Gap
* **Current Score**: {score}/{total} ({accuracy}% accuracy)
* **Strong Areas**: {strong_list}
* **Weak Areas**: {weak_list}
* **Learning Gap Analysis**: {f"You have a learning gap in {weak_count} topic(s). Focus on these specific areas to reach 100% mastery." if weak_topics else "No learning gap detected! All concepts mastered."}
* **History comparison**: {history if history else "This is your first attempt on this quiz topic."}

### 🚀 Next Steps & Timeline
* Re-study the marked concepts today, and take a follow-up quiz tomorrow to verify your progress!
"""

async def recommendation_node(state: AgentState) -> dict:
    logger.info("Recommendation Agent: Running...")
    weak_topics = state.get("weak_topics", [])
    strong_topics = state.get("strong_topics", []) or []
    score = state.get("score") or 0
    total = len(state.get("quiz_questions", [])) or 10
    user_id = state.get("user_id")
    
    # Query database for student history if available
    db = get_database()
    history_summary = ""
    try:
        if user_id:
            cursor = db.attempts.find({"user_id": user_id}).sort("attempted_at", -1)
            past_attempts = await cursor.to_list(length=3)
            if past_attempts:
                history_summary = "Past quiz performance scores: " + ", ".join([f"{att['score']}/{att['total_questions']}" for att in past_attempts])
    except Exception as e:
        logger.warning(f"Could not load past attempts for tutor recommendations: {e}")

    api_key = GEMINI_API_KEY or ""
    is_placeholder = any(x in api_key.lower() for x in ["placeholder", "your_actual", "here"]) or not api_key.strip()

    if is_placeholder:
        plan = get_fallback_study_plan(score, total, weak_topics, strong_topics, history_summary)
        return {"study_plan": plan}

    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        You are the Recommendation Agent (AI Tutor) in the QuizMaster AI platform.
        Your task is to analyze the student's quiz performance and write a highly personalized, actionable Markdown study plan.
        
        Quiz Score: {score}/{total}
        Strong Topics Identified: {', '.join(strong_topics) if strong_topics else 'None yet'}
        Weak Topics Identified: {', '.join(weak_topics) if weak_topics else 'None (Perfect Score!)'}
        {history_summary}
        
        Please generate a study plan structured with standard markdown headings:
        ### 📚 Personalized Study Plan
        - Provide numbered steps detailing what to study next (e.g. 1. Revise Graph Basics (30 minutes)).
        - Give exact study steps to help bridge the learning gap.
        
        ### ⏱️ Estimated Study Time
        - Estimate the total study time needed to complete this plan (e.g. Estimated Study Time: 2 Hours).
        
        ### 📊 Performance Summary & Learning Gap
        - Summarize the strong topics and identify the learning gap (what are they missing to get 100% score).
        
        ### 🚀 Next Steps & Timeline
        - Provide guidance on when to review the material again and when to take the next quiz.
        
        Keep the tone encouraging, supportive, and educational.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        plan = response.text
        return {"study_plan": plan}
        
    except Exception as e:
        logger.error(f"Error in Recommendation Agent: {e}. Falling back to local plan generator.")
        plan = get_fallback_study_plan(score, total, weak_topics, strong_topics, history_summary)
        return {"study_plan": plan}


async def progress_tracking_node(state: AgentState) -> dict:
    logger.info("Progress Tracking Agent: Running...")
    user_id = state.get("user_id")
    score = state.get("score") or 0
    total = len(state.get("quiz_questions", [])) or 10
    strong_topics = state.get("strong_topics", []) or []
    weak_topics = state.get("weak_topics", []) or []
    study_plan = state.get("study_plan", "") or "No custom plan generated."
    
    db = get_database()
    past_attempts = []
    try:
        if user_id:
            cursor = db.attempts.find({"user_id": user_id}).sort("attempted_at", -1)
            past_attempts = await cursor.to_list(length=10)
    except Exception as e:
        logger.warning(f"Could not fetch user attempt logs for progress tracking: {e}")
        
    # Calculate performance trend and study consistency
    # 1. Total quiz count
    total_quiz_count = len(past_attempts) + 1 # count current attempt
    
    # 2. Score trend (compare current attempt to average of past attempts)
    avg_past_score = 0
    trend_message = ""
    if past_attempts:
        past_scores = [att.get("score", 0) for att in past_attempts]
        avg_past_score = sum(past_scores) / len(past_scores)
        diff = score - avg_past_score
        if diff > 0:
            trend_message = f"Trending Up! You scored {diff:.1f} marks higher than your historical average."
        elif diff < 0:
            trend_message = f"Trending Down. You scored {abs(diff):.1f} marks below your average. Take some time to revise."
        else:
            trend_message = "Stable. Your score matches your historical average performance."
    else:
        trend_message = "Welcome to your first quiz! This is the start of your progress timeline tracking."
        
    api_key = GEMINI_API_KEY or ""
    is_placeholder = any(x in api_key.lower() for x in ["placeholder", "your_actual", "here"]) or not api_key.strip()

    if is_placeholder:
        # Fallback local analyzer summary
        summary = f"""**Analytics Report**
* **Progress Trend**: {trend_message}
* **Quizzes Completed**: {total_quiz_count}
* **Accuracy Streak**: Keep going to build your daily consistency streak!
"""
        return {
            "progress_logged": True,
            "progress_summary": summary
        }
        
    try:
        client = genai.Client(api_key=api_key)
        
        # Prepare context payload for Gemini
        attempts_context = []
        for a in past_attempts:
            attempts_context.append({
                "score": a.get("score"),
                "total": a.get("total_questions"),
                "weak_topics": a.get("weak_topics", []),
                "date": str(a.get("attempted_at"))
            })
            
        prompt = f"""
        You are the Progress Tracking Agent in the QuizMaster AI platform.
        Your task is to analyze the student's learning journey and write a highly motivating, short progress report (2-3 sentences).
        
        Current Quiz Attempt: Score {score}/{total}
        Strong Topics identified in this quiz: {', '.join(strong_topics) if strong_topics else 'None'}
        Weak Topics identified in this quiz: {', '.join(weak_topics) if weak_topics else 'None'}
        Tutor Study Plan Recommendation:
        {study_plan}
        
        Historical Attempts Logs:
        {json.dumps(attempts_context, indent=2)}
        
        Please provide a concise overview of their progress:
        - Identify if their score is improving compared to previous quizzes.
        - Highlight if they have cleared or still struggle with any specific weak topics based on these recommendations and history.
        - Encourage their consistency.
        
        Keep it encouraging and extremely short (max 80 words).
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        summary = response.text.strip()
        return {
            "progress_logged": True,
            "progress_summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error in Progress Tracking Agent: {e}. Falling back to local analyzer.")
        summary = f"""**Analytics Report**
* **Progress Trend**: {trend_message}
* **Quizzes Completed**: {total_quiz_count}
* **Accuracy Streak**: Keep practicing regularly to build your study streak!
"""
        return {
            "progress_logged": True,
            "progress_summary": summary
        }


# ================= Graph Compilation =================

# 1. Quiz Generation Workflow
quiz_gen_builder = StateGraph(AgentState)
quiz_gen_builder.add_node("analyze_content", analyze_content_node)
quiz_gen_builder.add_node("generate_quiz", generate_quiz_node)

quiz_gen_builder.set_entry_point("analyze_content")
quiz_gen_builder.add_edge("analyze_content", "generate_quiz")
quiz_gen_builder.add_edge("generate_quiz", END)

quiz_generation_graph = quiz_gen_builder.compile()

# 2. Quiz Evaluation Workflow
evaluation_builder = StateGraph(AgentState)
evaluation_builder.add_node("evaluate_answers", evaluate_answers_node)
evaluation_builder.add_node("recommendation", recommendation_node)
evaluation_builder.add_node("progress_tracking", progress_tracking_node)

evaluation_builder.set_entry_point("evaluate_answers")
evaluation_builder.add_edge("evaluate_answers", "recommendation")
evaluation_builder.add_edge("recommendation", "progress_tracking")
evaluation_builder.add_edge("progress_tracking", END)

quiz_evaluation_graph = evaluation_builder.compile()
