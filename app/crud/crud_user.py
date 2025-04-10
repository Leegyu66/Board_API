from datetime import timedelta
from fastapi import Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app import deps
from app.core import settings
from app.core.security import create_access_token
from app.db.base_class import Base

from typing import Optional

from sqlalchemy.orm import Session
from app.exceptions.custom_exception import BadRequestError
from app.models.user import User
from passlib.context import CryptContext

from app.schemas.token import Token


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CRUDUser():

    def __init__(self, model):
        self.model = model

    def get_by_id(self, db: Session, login_id: str) -> Optional[Base]:
        user = db.query(self.model).filter(self.model.login_id == login_id).first()
        return user

    def get_by_email(self, db: Session, email: str) -> Optional[Base]:
        user = db.query(self.model).filter(self.model.email == email).first()
        return user
    
    def create(self, db: Session, user_in: BaseModel) -> Base:

        if self.get_by_email(db, user_in.email):
            raise BadRequestError("Email is already in use.")
        
        user_in.password = pwd_context.hash(user_in.password)

        user = self.model(**user_in.dict())
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def login(self, response: Response, login_form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(deps.get_db)):
        user = self.get_by_email(db, login_form.username)

        if not user:
            raise BadRequestError("Invalid user or password")
        
        res = self.verify_password(login_form.password, user.password)

        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTE)
        access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

        response.set_cookie(key="access_token", value=access_token, expires=access_token_expires, httponly=False)

        if not res:
            raise BadRequestError("Invalid user or password")
        
        return Token(access_token=access_token, token_type="bearer")
    
    def verify_password(self, password, hashed_password):
        return pwd_context.verify(password, hashed_password)
    
    def is_superuser(self, user: User) -> bool:
        return user.is_superuser

user = CRUDUser(User)