from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.models import Role, Question, Interview, InterviewAnswer, User
from app.schemas.schemas import RoleResponse, QuestionResponse, SubmitInterviewRequest, DetailedResultResponse, AnswerDetailResponse, InterviewHistoryResponse
from app.api.user import get_current_user

router = APIRouter()

@router.get("/roles", response_model=List[RoleResponse])
def get_roles(db: Session = Depends(get_db)):
    return db.query(Role).all()

@router.get("/questions/{role_id}", response_model=List[QuestionResponse])
def get_questions_by_role(role_id: int, db: Session = Depends(get_db)):
    questions = db.query(Question).filter(Question.role_id == role_id).all()
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this role.")
    return questions

@router.post("/submit", response_model=DetailedResultResponse)
def submit_interview(payload: SubmitInterviewRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = db.query(Role).filter(Role.id == payload.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found.")

    questions = {q.id: q for q in db.query(Question).filter(Question.role_id == payload.role_id).all()}
    if not questions:
        raise HTTPException(status_code=400, detail="Invalid test attempt.")

    correct_count = 0
    answer_entries = []
    details = []

    for user_ans in payload.answers:
        q = questions.get(user_ans.question_id)
        if q:
            is_correct = (user_ans.selected_option.upper() == q.correct_option.upper())
            if is_correct:
                correct_count += 1
            
            answer_entries.append({
                "question_id": q.id,
                "selected_option": user_ans.selected_option.upper(),
                "is_correct": is_correct
            })

            details.append(AnswerDetailResponse(
                question_text=q.question_text,
                selected_option=user_ans.selected_option.upper(),
                correct_option=q.correct_option.upper(),
                is_correct=is_correct,
                option_a=q.option_a,
                option_b=q.option_b,
                option_c=q.option_c,
                option_d=q.option_d
            ))

    total_q = len(payload.answers)
    score_pct = round((correct_count / total_q) * 100, 2) if total_q > 0 else 0.0

    new_interview = Interview(
        user_id=current_user.id,
        role_id=payload.role_id,
        total_questions=total_q,
        correct_answers=correct_count,
        score_percentage=score_pct
    )
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)

    for entry in answer_entries:
        db.add(InterviewAnswer(
            interview_id=new_interview.id,
            question_id=entry["question_id"],
            selected_option=entry["selected_option"],
            is_correct=entry["is_correct"]
        ))
    db.commit()

    return DetailedResultResponse(
        interview_id=new_interview.id,
        role_title=role.title,
        total_questions=total_q,
        correct_answers=correct_count,
        score_percentage=score_pct,
        created_at=new_interview.created_at,
        details=details
    )

@router.get("/history", response_model=List[InterviewHistoryResponse])
def get_interview_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    interviews = db.query(Interview).filter(Interview.user_id == current_user.id).order_by(Interview.created_at.desc()).all()
    
    history = []
    for item in interviews:
        role = db.query(Role).filter(Role.id == item.role_id).first()
        history.append(InterviewHistoryResponse(
            id=item.id,
            role_title=role.title if role else "Unknown",
            score_percentage=float(item.score_percentage),
            created_at=item.created_at
        ))
    return history

@router.get("/result/{interview_id}", response_model=DetailedResultResponse)
def get_interview_result(interview_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    interview = db.query(Interview).filter(Interview.id == interview_id, Interview.user_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Result not found.")
    
    role = db.query(Role).filter(Role.id == interview.role_id).first()
    answers = db.query(InterviewAnswer).filter(InterviewAnswer.interview_id == interview.id).all()
    
    details = []
    for ans in answers:
        q = db.query(Question).filter(Question.id == ans.question_id).first()
        if q:
            details.append(AnswerDetailResponse(
                question_text=q.question_text,
                selected_option=ans.selected_option,
                correct_option=q.correct_option,
                is_correct=ans.is_correct,
                option_a=q.option_a,
                option_b=q.option_b,
                option_c=q.option_c,
                option_d=q.option_d
            ))

    return DetailedResultResponse(
        interview_id=interview.id,
        role_title=role.title if role else "Unknown",
        total_questions=interview.total_questions,
        correct_answers=interview.correct_answers,
        score_percentage=float(interview.score_percentage),
        created_at=interview.created_at,
        details=details
    )