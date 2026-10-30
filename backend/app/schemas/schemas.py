from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# --- Auth Schemas ---
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- User Profile Schemas ---
class UserProfile(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserProfileResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

# --- Interview & Role Schemas ---
class RoleResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    options: List[str]

    class Config:
        from_attributes = True

class AnswerSubmit(BaseModel):
    question_id: int
    selected_option: str

class SubmitInterviewRequest(BaseModel):
    role_id: int
    answers: List[AnswerSubmit]

class AnswerDetailResponse(BaseModel):
    question_id: int
    question_text: str
    selected_option: str
    correct_option: str
    is_correct: bool

class DetailedResultResponse(BaseModel):
    session_id: int
    role_title: str
    score: float
    total_questions: int
    correct_answers: int
    details: List[AnswerDetailResponse]

class InterviewHistoryResponse(BaseModel):
    session_id: int
    role_title: str
    score: float
    completed_at: datetime

    class Config:
        from_attributes = True