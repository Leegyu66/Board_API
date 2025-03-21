import sys
sys.path.insert(0, '/Users/ogq_gyn_in/dev/Board-API')

from sqlalchemy import Integer, String, Column, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class User(Base):
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(20), nullable=False)
    email = Column(String, nullable=True)
    login_id = Column(String(20), nullable=False)
    password = Column(String(30), nullable=False)
    reg_dt = Column(DateTime, nullable=False, default=datetime.now)
    is_superuser = Column(Boolean, default=False)
    boards = relationship(
        "Board",
        cascade="all,delete-orphan",
        back_populates="submitter",
        uselist=True)