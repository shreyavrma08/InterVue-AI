from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.db.session import get_db
import app.models.models as models

router = APIRouter()

# Pydantic Request Schemas
class RegisterSchema(BaseModel):
    email: EmailStr
    password: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(user_data: RegisterSchema, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
    
    # Create new user record
    new_user = models.User(
        email=user_data.email,
        hashed_password=user_data.password  # Passwords stored directly for testing
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    
    return {"message": "User registered successfully", "user_id": new_user.id}

@router.post("/login")
def login(user_data: LoginSchema, db: Session = Depends(get_db)):
    # Authenticate user
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    
    if not user or user.hashed_password != user_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Return dummy token and user info
    return {
        "access_token": f"fake-jwt-token-{user.id}",
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email
    }