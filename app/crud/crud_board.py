from pydantic import BaseModel
from app.models.board import Board
from app.schemas.board import BoardCreate, BoardUpdate, BoardDelete, BoardInDBBase
from sqlalchemy.orm import Session 
from app.db.base_class import Base
from sqlalchemy import and_
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from app.models.user import User
import pytz

from typing import Any, Optional, List

class CRUDBoard():

    def __init__(self, model):
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[Base]:
        post = db.query(self.model).filter(self.model.id == id).first()

        if not post or post.del_yn != "N":
            raise ValueError("Board does not exist")

        self.update_view_id(db, post)
        return post
        
    def get_multi(
        self, 
        db: Session
    ) -> List[Base]:
        lists = db.query(self.model).filter(self.model.del_yn == 'N').all()
        return [BoardInDBBase(id=list.id, title=list.title, content=list.content, view_cnt=list.view_cnt, reg_dt=list.reg_dt, mdf_dt=list.mdf_dt, submitter_id=list.submitter_id) for list in lists]
    
    def create_board(self, db: Session, *, board_in: BaseModel) -> Base:
        # obj_in_data = jsonable_encoder(board_in)
        # db_obj = self.model(**obj_in_data)
        # db.add(db_obj)
        # db.commit()
        # db.refresh(db_obj)

        user = db.query(User).filter(User.id == board_in.submitter_id).first()

        if not user:
            raise ValueError("User not found")
        
        board = self.model(**board_in.dict())
        db.add(board)
        db.commit()
        db.refresh(board)
        return board
    
    def update_view_id(self, db: Session, board: Board) -> None:
        board.view_cnt += 1
        db.commit()
        db.refresh(board)

    def delete(self, db: Session, board_id: int) -> Base:
        board = db.query(self.model).filter(self.model.id == board_id).first()
        if not board or board.del_yn == "Y":
            raise ValueError("Board does not exists")

        board.del_yn = "Y"
        db.commit()
        db.refresh(board)

        return board
    
    def delete_hard(self, db: Session, board_id: int) -> Base:
        board = db.query(self.model).filter(self.model.id == board_id).first()
        if not board:
            raise ValueError("Board does not exists")
        db.delete(board)
        db.commit()
        return {"message": "삭제 완료"}
    
    def update_board(self, db: Session, board_id, board_update) -> Base:
        board = db.query(self.model).filter(and_(self.model.id == board_id, self.model.del_yn == "N")).first()

        if not board:
            raise ValueError("Board does not exist")

        board.title = board_update.title
        board.content = board_update.content
        board.mdf_dt = datetime.now(pytz.timezone("Asia/Seoul"))
        db.commit()
        db.refresh(board)
        return board   

    def get_user_posts(self, db: Session, user_id: int) -> List[Base]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        lists = db.query(Board).filter(Board.del_yn == "N", Board.submitter_id == user.id).all()
        return [BoardInDBBase (id=list.id, title=list.title, content=list.content, view_cnt=list.view_cnt, reg_dt=list.reg_dt, mdf_dt=list.mdf_dt, submitter_id=list.submitter_id) for list in lists]     
        

board = CRUDBoard(Board)