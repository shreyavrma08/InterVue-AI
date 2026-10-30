import os
import sys
import json
import math
import random
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import requests

# Set project root (backend folder) into sys.path before local imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Import initialize_database directly from init_db.py
try:
    from init_db import initialize_database
except ImportError:
    import init_db
    initialize_database = init_db.initialize_database
engine = create_engine(DB_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")

app = FastAPI(title="AI Interviewer Core Engine API")

# Enable CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Event: Automatically verify & seed database schema on server launch
@app.on_event("startup")
def on_startup():
    try:
        initialize_database()
        print("Database initialized successfully on startup.")
    except Exception as e:
        print(f"Database auto-initialization skipped or failed: {str(e)}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fake Auth Extractor (Integration mock using existing JWT mechanism)
def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    if not authorization:
        return 1  # Fallback default user for testing
    try:
        token = authorization.split(" ")[1]
        return 1
    except Exception:
        return 1

# --- PYDANTIC SCHEMAS ---
class OptionSubmit(BaseModel):
    option_id: Optional[int]

class AnswerSubmission(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None

class AssessmentSubmitRequest(BaseModel):
    assessment_id: int
    answers: List[AnswerSubmission]

class AIQuestionGenRequest(BaseModel):
    topic_id: int
    difficulty: str
    num_questions: int = 5

class AIPersonalizedGenRequest(BaseModel):
    subject_id: int


# --- ROOT ROUTE ---
@app.get("/")
def read_root():
    return {"message": "AI Interviewer API is running successfully!"}


# --- TOPICS & SUBJECTS API ---
@app.get("/api/admin/topics")
def get_all_topics(db: Session = Depends(get_db)):
    """Fetch all topics along with their parent subject names for admin dropdowns."""
    query = text("""
        SELECT t.id AS topic_id, t.name AS topic_name, s.name AS subject_name 
        FROM topics t 
        JOIN subjects s ON t.subject_id = s.id
        ORDER BY s.name, t.name
    """)
    rows = db.execute(query).fetchall()
    
    return [
        {
            "topic_id": r.topic_id,
            "topic_name": r.topic_name,
            "subject_name": r.subject_name
        }
        for r in rows
    ]


# --- ASSESSMENT ENGINE LOGIC ---
@app.post("/api/assessment/start")
def start_assessment(
    subject_id: int, 
    total_questions: int = 20, 
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    topics = db.execute(
        text("SELECT id FROM topics WHERE subject_id = :sid"), {"sid": subject_id}
    ).fetchall()
    
    if not topics:
        raise HTTPException(status_code=404, detail="No topics found for this subject.")
    
    topic_ids = [t[0] for t in topics]
    
    target_basic = math.ceil(total_questions * 0.30)
    target_inter = math.floor(total_questions * 0.40)
    target_adv = total_questions - (target_basic + target_inter)
    
    selected_question_ids = []
    
    def fetch_balanced_questions(diff: str, target_count: int) -> List[int]:
        if target_count <= 0:
            return []
        
        questions_per_topic = math.ceil(target_count / len(topic_ids))
        pool = []
        for tid in topic_ids:
            q_rows = db.execute(
                text("""
                    SELECT id FROM questions 
                    WHERE topic_id = :tid AND difficulty = :diff AND is_active = TRUE 
                    ORDER BY RAND() LIMIT :lim
                """),
                {"tid": tid, "diff": diff, "lim": questions_per_topic}
            ).fetchall()
            pool.extend([q[0] for q in q_rows])
            
        random.shuffle(pool)
        
        if len(pool) < target_count:
            existing_ids = tuple(pool) if pool else (-1,)
            extra_rows = db.execute(
                text(f"""
                    SELECT id FROM questions 
                    WHERE topic_id IN ({','.join(map(str, topic_ids))}) 
                    AND difficulty = :diff AND is_active = TRUE 
                    AND id NOT IN :existing
                    ORDER BY RAND() LIMIT :lim
                """),
                {"diff": diff, "existing": existing_ids, "lim": target_count - len(pool)}
            ).fetchall()
            pool.extend([q[0] for q in extra_rows])
            
        return pool[:target_count]

    selected_question_ids.extend(fetch_balanced_questions("basic", target_basic))
    selected_question_ids.extend(fetch_balanced_questions("intermediate", target_inter))
    selected_question_ids.extend(fetch_balanced_questions("advanced", target_adv))
    
    random.shuffle(selected_question_ids)
    
    if not selected_question_ids:
        raise HTTPException(status_code=400, detail="Insufficient questions in bank for this assessment.")

    res = db.execute(
        text("""
            INSERT INTO assessments (user_id, subject_id, total_questions, duration_minutes, status) 
            VALUES (:uid, :sid, :tq, 30, 'in_progress')
        """),
        {"uid": user_id, "sid": subject_id, "tq": len(selected_question_ids)}
    )
    db.commit()
    assessment_id = res.lastrowid

    for idx, qid in enumerate(selected_question_ids, 1):
        db.execute(
            text("""
                INSERT INTO assessment_questions (assessment_id, question_id, question_order)
                VALUES (:aid, :qid, :ord)
            """),
            {"aid": assessment_id, "qid": qid, "ord": idx}
        )
    db.commit()

    return {"assessment_id": assessment_id, "total_questions": len(selected_question_ids)}


@app.get("/api/assessment/{assessment_id}/questions")
def get_assessment_questions(assessment_id: int, db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT q.id, q.question_text, q.difficulty, aq.question_order, t.name as topic_name
            FROM assessment_questions aq
            JOIN questions q ON aq.question_id = q.id
            JOIN topics t ON q.topic_id = t.id
            WHERE aq.assessment_id = :aid
            ORDER BY aq.question_order ASC
        """),
        {"aid": assessment_id}
    ).fetchall()

    questions = []
    for row in rows:
        options = db.execute(
            text("SELECT id, option_text FROM question_options WHERE question_id = :qid"),
            {"qid": row.id}
        ).fetchall()
        
        questions.append({
            "id": row.id,
            "order": row.question_order,
            "text": row.question_text,
            "difficulty": row.difficulty,
            "topic": row.topic_name,
            "options": [{"id": o.id, "text": o.option_text} for o in options]
        })

    return {"assessment_id": assessment_id, "questions": questions}


@app.post("/api/assessment/submit")
def submit_assessment(data: AssessmentSubmitRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM user_answers WHERE assessment_id = :aid"), {"aid": data.assessment_id})
    
    attempted = 0
    correct = 0
    
    for ans in data.answers:
        is_correct = False
        if ans.selected_option_id:
            attempted += 1
            check = db.execute(
                text("SELECT is_correct FROM question_options WHERE id = :oid AND question_id = :qid"),
                {"oid": ans.selected_option_id, "qid": ans.question_id}
            ).fetchone()
            if check and check[0]:
                is_correct = True
                correct += 1

        db.execute(
            text("""
                INSERT INTO user_answers (assessment_id, question_id, selected_option_id, is_correct)
                VALUES (:aid, :qid, :soid, :ic)
            """),
            {"aid": data.assessment_id, "qid": ans.question_id, "soid": ans.selected_option_id, "ic": is_correct}
        )
        
    total_qs = len(data.answers)
    incorrect = attempted - correct
    unattempted = total_qs - attempted
    score = (correct / total_qs) * 100 if total_qs > 0 else 0
    accuracy = (correct / attempted) * 100 if attempted > 0 else 0

    db.execute(
        text("""
            INSERT INTO results (assessment_id, user_id, score, accuracy_rate, total_questions, attempted_questions, correct_answers, incorrect_answers, unattempted_questions)
            VALUES (:aid, :uid, :sc, :acc, :tq, :att, :ca, :ia, :ua)
        """),
        {
            "aid": data.assessment_id, "uid": user_id, "sc": score, "acc": accuracy,
            "tq": total_qs, "att": attempted, "ca": correct, "ia": incorrect, "ua": unattempted
        }
    )
    
    db.execute(
        text("UPDATE assessments SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = :aid"),
        {"aid": data.assessment_id}
    )
    db.commit()

    return {"status": "success", "assessment_id": data.assessment_id}


@app.get("/api/results/{assessment_id}")
def get_assessment_result(assessment_id: int, db: Session = Depends(get_db)):
    result = db.execute(
        text("SELECT * FROM results WHERE assessment_id = :aid"), {"aid": assessment_id}
    ).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Result report not found.")

    breakdown_rows = db.execute(
        text("""
            SELECT t.name as topic_name, q.difficulty, ua.is_correct
            FROM user_answers ua
            JOIN questions q ON ua.question_id = q.id
            JOIN topics t ON q.topic_id = t.id
            WHERE ua.assessment_id = :aid
        """),
        {"aid": assessment_id}
    ).fetchall()

    topic_stats = {}
    diff_stats = {"basic": {"total": 0, "correct": 0}, "intermediate": {"total": 0, "correct": 0}, "advanced": {"total": 0, "correct": 0}}

    for row in breakdown_rows:
        tname = row.topic_name
        diff = row.difficulty
        ic = row.is_correct

        if tname not in topic_stats:
            topic_stats[tname] = {"total": 0, "correct": 0}
        topic_stats[tname]["total"] += 1
        if ic:
            topic_stats[tname]["correct"] += 1

        if diff in diff_stats:
            diff_stats[diff]["total"] += 1
            if ic:
                diff_stats[diff]["correct"] += 1

    return {
        "assessment_id": result.assessment_id,
        "score": float(result.score),
        "accuracy_rate": float(result.accuracy_rate),
        "total": result.total_questions,
        "attempted": result.attempted_questions,
        "correct": result.correct_answers,
        "incorrect": result.incorrect_answers,
        "unattempted": result.unattempted_questions,
        "topic_breakdown": topic_stats,
        "difficulty_breakdown": diff_stats
    }


# --- USER DASHBOARD ANALYTICS ---
@app.get("/api/dashboard/analytics")
def get_dashboard_analytics(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    history = db.execute(
        text("""
            SELECT r.score, r.accuracy_rate, r.generated_at, s.name as subject_name
            FROM results r
            JOIN assessments a ON r.assessment_id = a.id
            JOIN subjects s ON a.subject_id = s.id
            WHERE r.user_id = :uid
            ORDER BY r.generated_at ASC
        """),
        {"uid": user_id}
    ).fetchall()

    topic_performance = db.execute(
        text("""
            SELECT t.name as topic_name, 
                   COUNT(ua.id) as total_answers,
                   SUM(CASE WHEN ua.is_correct = TRUE THEN 1 ELSE 0 END) as correct_answers
            FROM user_answers ua
            JOIN questions q ON ua.question_id = q.id
            JOIN topics t ON q.topic_id = t.id
            JOIN assessments a ON ua.assessment_id = a.id
            WHERE a.user_id = :uid
            GROUP BY t.id, t.name
        """),
        {"uid": user_id}
    ).fetchall()

    strong_topics = []
    weak_topics = []

    for row in topic_performance:
        acc = (row.correct_answers / row.total_answers) * 100 if row.total_answers > 0 else 0
        item = {"topic": row.topic_name, "accuracy": round(acc, 1)}
        if acc >= 70:
            strong_topics.append(item)
        else:
            weak_topics.append(item)

    return {
        "strong_topics": strong_topics,
        "weak_topics": weak_topics,
        "progress_history": [
            {"subject": h.subject_name, "score": float(h.score), "accuracy": float(h.accuracy_rate), "date": str(h.generated_at)}
            for h in history
        ]
    }


# --- ADMIN AI QUESTION GENERATOR ---
@app.post("/api/admin/ai/generate")
def generate_ai_questions(req: AIQuestionGenRequest, db: Session = Depends(get_db)):
    topic_row = db.execute(text("SELECT name FROM topics WHERE id = :tid"), {"tid": req.topic_id}).fetchone()
    if not topic_row:
        raise HTTPException(status_code=404, detail="Topic ID invalid.")
    
    topic_name = topic_row[0]

    prompt = f"""
    Generate {req.num_questions} multiple-choice question(s) for technical interview preparation.
    Topic: '{topic_name}'
    Difficulty: '{req.difficulty}'

    OUTPUT STRICT JSON ONLY array matching this exact schema:
    [
      {{
        "question_text": "Question statement here",
        "difficulty": "{req.difficulty}",
        "explanation": "Detailed answer rationale",
        "options": [
          {{"text": "Option A", "is_correct": true}},
          {{"text": "Option B", "is_correct": false}},
          {{"text": "Option C", "is_correct": false}},
          {{"text": "Option D", "is_correct": false}}
        ]
      }}
    ]
    """

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=30)
        raw_json = response.json()['choices'][0]['message']['content']
        questions = json.loads(raw_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM API Generation Error: {str(e)}")

    staged_ids = []
    for q in questions:
        is_valid = True
        reason = "Passed integrity checks"
        
        correct_count = sum(1 for o in q.get('options', []) if o.get('is_correct') is True)
        if len(q.get('options', [])) != 4:
            is_valid = False
            reason = "Question must have exactly 4 options"
        elif correct_count != 1:
            is_valid = False
            reason = f"Must have exactly 1 correct answer (found {correct_count})"

        res = db.execute(
            text("""
                INSERT INTO ai_question_staging (topic_id, question_text, difficulty, options_json, explanation, validation_status, validation_reason)
                VALUES (:tid, :qt, :diff, :opts, :exp, :vstat, :vreas)
            """),
            {
                "tid": req.topic_id, "qt": q['question_text'], "diff": req.difficulty,
                "opts": json.dumps(q['options']), "exp": q.get('explanation', ''),
                "vstat": "valid" if is_valid else "invalid", "vreas": reason
            }
        )
        staged_ids.append(res.lastrowid)
        
    db.commit()
    return {"message": f"Successfully generated & staged {len(staged_ids)} questions.", "staged_ids": staged_ids}


@app.get("/api/admin/ai/staged")
def get_staged_questions(db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT s.*, t.name as topic_name 
            FROM ai_question_staging s 
            JOIN topics t ON s.topic_id = t.id 
            WHERE s.status = 'staged'
        """)
    ).fetchall()

    return [
        {
            "id": r.id,
            "topic_name": r.topic_name,
            "question_text": r.question_text,
            "difficulty": r.difficulty,
            "options": json.loads(r.options_json),
            "explanation": r.explanation,
            "validation_status": r.validation_status,
            "validation_reason": r.validation_reason
        } for r in rows
    ]


@app.post("/api/admin/ai/approve/{staged_id}")
def approve_staged_question(staged_id: int, db: Session = Depends(get_db)):
    staged = db.execute(text("SELECT * FROM ai_question_staging WHERE id = :sid"), {"sid": staged_id}).fetchone()
    if not staged or staged.status != 'staged':
        raise HTTPException(status_code=404, detail="Staged item not found or already processed.")

    q_res = db.execute(
        text("""
            INSERT INTO questions (topic_id, question_text, difficulty, explanation, source)
            VALUES (:tid, :qt, :diff, :exp, 'ai_generated')
        """),
        {"tid": staged.topic_id, "qt": staged.question_text, "diff": staged.difficulty, "exp": staged.explanation}
    )
    new_q_id = q_res.lastrowid

    options = json.loads(staged.options_json)
    for opt in options:
        db.execute(
            text("INSERT INTO question_options (question_id, option_text, is_correct) VALUES (:qid, :ot, :ic)"),
            {"qid": new_q_id, "ot": opt['text'], "ic": opt['is_correct']}
        )

    db.execute(text("UPDATE ai_question_staging SET status = 'approved' WHERE id = :sid"), {"sid": staged_id})
    db.commit()

    return {"message": "Question approved and migrated to active production bank."}


# --- PERSONALIZED WEAK TOPIC ASSESSMENT ---
@app.post("/api/assessment/personalized")
def generate_personalized_assessment(
    req: AIPersonalizedGenRequest, 
    user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    weak_rows = db.execute(
        text("""
            SELECT t.id, t.name, 
                   SUM(CASE WHEN ua.is_correct = TRUE THEN 1 ELSE 0 END) / COUNT(ua.id) as accuracy
            FROM user_answers ua
            JOIN questions q ON ua.question_id = q.id
            JOIN topics t ON q.topic_id = t.id
            WHERE t.subject_id = :sid AND ua.assessment_id IN (
                SELECT id FROM assessments WHERE user_id = :uid
            )
            GROUP BY t.id, t.name
            HAVING accuracy < 0.70
        """),
        {"sid": req.subject_id, "uid": user_id}
    ).fetchall()

    if not weak_rows:
        return start_assessment(subject_id=req.subject_id, total_questions=20, user_id=user_id, db=db)

    weak_topic_ids = [r.id for r in weak_rows]
    
    q_rows = db.execute(
        text(f"""
            SELECT id FROM questions 
            WHERE topic_id IN ({','.join(map(str, weak_topic_ids))})
            AND difficulty IN ('intermediate', 'advanced') AND is_active = TRUE
            ORDER BY RAND() LIMIT 20
        """)
    ).fetchall()

    selected_ids = [q[0] for q in q_rows]
    if not selected_ids:
        raise HTTPException(status_code=400, detail="Insufficient targeted weak topic questions available.")

    res = db.execute(
        text("""
            INSERT INTO assessments (user_id, subject_id, assessment_type, total_questions, duration_minutes) 
            VALUES (:uid, :sid, 'ai_personalized', :tq, 30)
        """),
        {"uid": user_id, "sid": req.subject_id, "tq": len(selected_ids)}
    )
    db.commit()
    assessment_id = res.lastrowid

    for idx, qid in enumerate(selected_ids, 1):
        db.execute(
            text("INSERT INTO assessment_questions (assessment_id, question_id, question_order) VALUES (:aid, :qid, :ord)"),
            {"aid": assessment_id, "qid": qid, "ord": idx}
        )
    db.commit()

    return {"assessment_id": assessment_id, "type": "ai_personalized", "total_questions": len(selected_ids)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)