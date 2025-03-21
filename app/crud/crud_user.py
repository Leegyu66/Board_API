import sys

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.db.base_class import Base
sys.path.insert(0, '/Users/ogq_gyn_in/dev/Board-API')

from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class CRUDUser():

    def __init__(self, model):
        self.model = model

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        return super().update(db, db_obj=db_obj, obj_in=update_data)
    
    def create(self, db: Session, *, obj_in: BaseModel) -> Base:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def is_superuser(self, user: User) -> bool:
        return user.is_superuser

user = CRUDUser(User)