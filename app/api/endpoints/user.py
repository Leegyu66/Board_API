from fastapi import APIRouter, Depends, Request

from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.schemas.user import UserCreate, UserInDB
from app.schemas.token import Token
from app import deps
from app import crud

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Response

api_router = APIRouter()

@api_router.get("", status_code=200, response_model=UserInDB)
def get_login_user(
    current_user = Depends(get_current_user),
    db: Session = Depends(deps.get_db)
) -> dict:
    return current_user

@api_router.post("", status_code=201, response_model=UserCreate)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> dict:
    
    user = crud.user.create(db=db, user_in=user_in)
    return user

@api_router.post("/login", status_code=200)
def login(
    response: Response,
    login_form: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(deps.get_db),
) -> Token:

    token = crud.user.login(response=response, login_form=login_form, db=db)
    return token

@api_router.post("/logout", status_code=200)
def logout(
    response: Response,
    request: Request
) -> None:
    
    # access_token = request.cookies.get("access_token")
    response.delete_cookie(key="access_token")
    return {"message": "success"}