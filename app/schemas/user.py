from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator
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
    name: str
    email: EmailStr
    login_id: str
    password: str

    @field_validator('email', 'name', 'password')
    @classmethod
    def check_empty(cls, v, field):
        if not v or v.isspace():
            raise ValueError("항목은 비어 있을 수 없습니다.")
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("비밀번호는 최소 8자 이상이어야 합니다.")
        
        if not any(char.isdigit() for char in v):
            raise ValueError("비밀번호에는 최소 하나 이상의 숫자가 포함되어야 합니다.")
        
        if not any(char.isalpha() for char in v):
            raise ValueError("비밀번호에는 최소 하나 이상의 영문자가 포함되어야 합니다.")
        
        return v


class UserInDBBase(UserBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

class User(UserInDBBase):
    pass