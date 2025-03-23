from fastapi import APIRouter, HTTPException, Depends

from sqlalchemy.orm import Session

from app.schemas.user import UserCreate
from app import deps
from app import crud

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import status

api_router = APIRouter()

@api_router.post("/", status_code=201, response_model=UserCreate)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> dict:
    
    user = crud.user.create(db=db, user_in=user_in)
    return user

@api_router.post("/login", status_code=200)
def login(
    login_form: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(deps.get_db),
) -> dict:
    
    user = crud.user.get_by_email(db, login_form.username)

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user or password")
    
    res = crud.user.verify_password(login_form.password, user.password)

    if not res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user or password")
    
    return {"message": "Login successful", "user_id": user.id}