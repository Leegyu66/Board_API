from pydantic import BaseModel

from app.db.base_class import Base

from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session
from app.models.user import User
from passlib.context import CryptContext

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
    
    # def update(
    #     self, db: Session, db_obj: User, obj_in: Union[Dict[str, Any]]
    # ) -> User:
    #     if isinstance(obj_in, dict):
    #         update_data = obj_in
    #     else:
    #         update_data = obj_in.dict(exclude_unset=True)

    #     return super().update(db, db_obj=db_obj, obj_in=update_data)
    
    def create(self, db: Session, user_in: BaseModel) -> Base:

        if self.get_by_email(db, user_in.email):
            raise ValueError("Email is already in use.")

        if self.get_by_id(db, user_in.login_id):
            raise ValueError("Login ID is already in use.")
        
        user_in.password = pwd_context.hash(user_in.password)

        user = self.model(**user_in.dict())
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def verify_password(self, password, hashed_password):
        return pwd_context.verify(password, hashed_password)
    
    def is_superuser(self, user: User) -> bool:
        return user.is_superuser

user = CRUDUser(User)