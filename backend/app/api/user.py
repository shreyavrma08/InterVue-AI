from fastapi import APIRouter
router = APIRouter()
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import UserProfileResponse, UserProfileUpdate
from app.core.config import settings

router = APIRouter()

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized access")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/profile", response_model=UserProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserProfileResponse)
def update_profile(profile_data: UserProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.name = profile_data.name
    current_user.phone = profile_data.phone
    current_user.education = profile_data.education
    current_user.skills = profile_data.skills
    db.commit()
    db.refresh(current_user)
    return current_user