from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator, Field

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

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    login_id: str
    password: str
    is_superuser: bool = False

    @field_validator('email', 'name', 'password')
    @classmethod
    def check_empty(cls, v):
        if not v or v.isspace():
            raise ValueError(f"field cannot be empty")
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one alphabetical character")
        
        return v


class UserInDB(BaseModel):
    id: Optional[int] = None
    name: str
    email: EmailStr
    login_id: str
    password: str
    is_superuser: bool = False

    class Config:
        orm_mode = True
