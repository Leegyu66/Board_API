from sqlalchemy import Integer, String, Column, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz

from app.db.base_class import Base

class Board(Base):
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    content = Column(String(1000), nullable=True)
    view_cnt = Column(Integer, nullable=False, default=0)
    del_yn = Column(String(2), nullable=False, default="N")
    reg_dt = Column(DateTime, nullable=False)
    mdf_dt = Column(DateTime, nullable=True)
    submitter_id = Column(Integer, ForeignKey("user.id"))
    submitter = relationship("User", back_populates="boards")