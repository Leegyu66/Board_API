from typing import Optional

from pydantic import BaseModel, EmailStr
from sqlalchemy import Boolean

'''
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(20), nullable=False)
    email = Column(String, nullable=True)
    login_id = Column(String(20), nullable=False)
    password = Column(String(30), nullable=False)
    reg_dt = Column(DateTime, nullable=False)
    mdf_dt = Column(DateTime, nullable=True)
    boards = relationship(
        "Board",
        cascade="all,delete-orphan",
        back_populates="submitter",
        uselist=True)
'''

class UserBase(BaseModel):
    name: str
    login_id: str
    password: str
    is_superuser: bool

class UserCreate(UserBase):
    email: EmailStr

class UserUpdate(UserBase):
    ...

class UserInDBBase(UserBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

class User(UserInDBBase):
    pass