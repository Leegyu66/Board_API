from fastapi import APIRouter, Depends

from typing import List
from sqlalchemy.orm import Session

from app.schemas.board import BoardInDB, BoardCreate, BoardUpdate
from app import deps
from app import crud
from app.core.auth import get_current_user

api_router = APIRouter()

# 게시판 읽기 - 1
@api_router.get("", status_code=200)
def read_board(
    db: Session = Depends(deps.get_db)
) -> List:
    
    lists = crud.board.get_multi(db=db)
    return lists

# 게시판 읽기 - 2
@api_router.get("/{board_id}", status_code=200, response_model=BoardInDB)
def fetch_board(
    board_id: int,
    db: Session = Depends(deps.get_db)
) -> dict:

    result = crud.board.get(db=db, id=board_id)
    return result


# 게시판 읽기 - 3
@api_router.get("/user/{user_id}", status_code=200, response_model=List[BoardInDB])
def get_user_posts(
    user_id: int,
    db: Session = Depends(deps.get_db)
) -> List[BoardInDB]:
    
    boards = crud.board.get_user_posts(db=db, user_id=user_id)
    return boards

# 게시판 쓰기
@api_router.post("", status_code=201, response_model=BoardInDB)
def create_board(
    board_in: BoardCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
) -> BoardInDB:
    
    board = crud.board.create_board(db=db, board_in=board_in, current_user=current_user)
    return board
    
# 게시판 수정
@api_router.patch("/{board_id}", status_code=200, response_model=BoardInDB)
def update_board(
    board_id: int,
    board_in: BoardUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
) -> BoardInDB:
    
    board = crud.board.update_board(db=db, board_id=board_id, board_update=board_in, current_user=current_user)
    return board


# 게시판 삭제
@api_router.delete("/{board_id}", status_code=200, response_model=BoardInDB)
def delete_board(
    board_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
) -> BoardInDB:
    
    board = crud.board.delete(db=db, board_id=board_id, current_user=current_user)
    return board


@api_router.delete("/{board_id}/hard", status_code=200, response_model=dict)
def delete_board_hard(
    board_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(get_current_user)
) -> dict:
    
    board = crud.board.delete_hard(db=db, board_id=board_id, current_user=current_user)
    return board