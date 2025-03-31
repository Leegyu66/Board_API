from pydantic import BaseModel
from app.exceptions.custom_exception import Forbidden, NotFoundError
from app.models.board import Board
from app.schemas.board import BoardInDB, BoardUpdate
from sqlalchemy.orm import Session 
from app.db.base_class import Base
from sqlalchemy import and_
from datetime import datetime
from app.models.user import User
import pytz

from typing import Optional, List

class CRUDBoard():

    def __init__(self, model):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[Base]:
        board = db.query(self.model).filter(self.model.id == id).first()

        if not board or board.del_yn != "N":
            raise NotFoundError("Board does not exist")

        self.update_view_id(db, board)
        return board
        
    def get_multi(self, db: Session) -> List[Base]:
        lists = db.query(self.model).filter(self.model.del_yn == 'N').all()
        return [BoardInDB(id=list.id, title=list.title, content=list.content, view_cnt=list.view_cnt, reg_dt=list.reg_dt, mdf_dt=list.mdf_dt, del_yn=list.del_yn, submitter_id=list.submitter_id) for list in lists]
    
    def create_board(self, db: Session, *, board_in: BaseModel, current_user) -> Base:
        
        board = self.model(**board_in.dict())
        board.submitter_id = current_user.id
        board.reg_dt = datetime.now(pytz.timezone("Asia/Seoul"))
        db.add(board)
        db.commit()
        db.refresh(board)
        return board
    
    def update_view_id(self, db: Session, board: Board) -> None:
        board.view_cnt += 1
        db.commit()
        db.refresh(board)

    def delete(self, db: Session, board_id: int, current_user: User) -> Base:
        board = db.query(self.model).filter(and_(self.model.id == board_id, self.model.del_yn == "N")).first()
        if not board:
            raise NotFoundError("Board does not exists")
        
        if board.submitter_id != current_user.id:
            raise Forbidden("You do not have permission to update this board")

        board.del_yn = "Y"
        db.commit()
        db.refresh(board)

        return board
    
    def delete_hard(self, db: Session, board_id: int, current_user: User) -> Base:
        board = db.query(self.model).filter(self.model.id == board_id).first()

        if not board:
            raise NotFoundError("Board does not exists")

        if board.submitter_id != current_user.id:
            raise Forbidden("You do not have permission to update this board")
        
        db.delete(board)
        db.commit()
        return {"message": "delete complete"}
    
    def update_board(self, db: Session, board_id: int, board_update: BoardUpdate, current_user: User) -> Base:
        board = db.query(self.model).filter(and_(self.model.id == board_id, self.model.del_yn == "N")).first()

        if not board:
            raise NotFoundError("Board does not exist")
        
        if board.submitter_id != current_user.id:
            raise Forbidden("You do not have permission to update this board")

        board.title = board_update.title
        board.content = board_update.content
        board.mdf_dt = datetime.now(pytz.timezone("Asia/Seoul"))
        db.commit()
        db.refresh(board)
        return board   

    def get_user_posts(self, db: Session, user_id: int) -> List[Base]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")

        lists = db.query(Board).filter(Board.del_yn == "N", Board.submitter_id == user.id).all()
        return [BoardInDB(id=list.id, title=list.title, content=list.content, view_cnt=list.view_cnt, reg_dt=list.reg_dt, mdf_dt=list.mdf_dt, submitter_id=list.submitter_id) for list in lists]     
        

board = CRUDBoard(Board)