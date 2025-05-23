from datetime import datetime
from pydantic import BaseModel
from typing import Optional

'''
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    content = Column(String(1000), nullable=True)
    view_cnt = Column(int, nullable=False, default=0)
    del_yn = Column(int, nullable=False, default=0)
    reg_dt = Column(DateTime, nullable=False)
    mdf_dt = Column(DateTime, nullable=True)
    submitter_id = Column(int, ForeignKey("user.id"))
    submitter = relationship("User", backpopulates="boards")
'''

class BoardCreate(BaseModel):
    title: str
    content: Optional[str] = None

class BoardUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class BoardDelete(BaseModel):
    id: int
    del_yn: str

class BoardInDB(BaseModel):
    id: int
    title: str
    content: Optional[str] = None
    view_cnt: int
    reg_dt: datetime
    mdf_dt: Optional[datetime] = None
    submitter_id: int

    class Config:
        orm_mode = True

class BoardInDB_with_username(BoardInDB):
    name: str