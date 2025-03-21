import sys

sys.path.insert(0, '/Users/ogq_gyn_in/dev/Board-API')

from fastapi import FastAPI, APIRouter, Query, HTTPException, Request, Depends
from fastapi.templating import Jinja2Templates

from typing import Optional, Any, List
from pathlib import Path
from sqlalchemy.orm import Session

from app.schemas.board import Board, BoardCreate, BoardUpdate, BoardInDBBase
from app.schemas.user import User
from app import deps
from app import crud

from datetime import datetime


app = FastAPI(title="Recipe API", openapi_url="/openapi.json")

api_router = APIRouter()


@api_router.get("/", status_code=200)
def root() -> dict:
    return {"title": "게시판 API"}

# 게시판 읽기 - 1
@api_router.get("/board", status_code=200)
def read_board(
    *,
    db: Session = Depends(deps.get_db),
) -> List:
    lists = crud.board.get_multi(db)
    return lists

# 게시판 읽기 - 2
@api_router.get("/board/{board_id}", status_code=200, response_model=BoardInDBBase)
def fetch_board(
    *,
    board_id: int,
    db: Session = Depends(deps.get_db),
) -> dict:
    
    try:
        result = crud.board.get(db=db, id=board_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        

# 게시판 쓰기
@api_router.post("/board/", status_code=201, response_model=Board)
def create_board(
    *,
    board_in: BoardCreate,
    db: Session = Depends(deps.get_db)
) -> dict:
    
    try:
        board = crud.board.create_board(db=db, board_in=board_in)
        return board
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# 게시판 수정
@api_router.patch("/board/{board_id}", status_code=200, response_model=Board)
def update_board(
    board_id: int,
    board_in: BoardUpdate,
    db: Session = Depends(deps.get_db),
) -> dict:
    
    try:
        board = crud.board.update_board(db=db, board_id=board_id, board_update=board_in)
        return board
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# 게시판 삭제
@api_router.delete("/board/{board_id}", status_code=200, response_model=Board)
def delete_board(
    *,
    board_id: int,
    db: Session = Depends(deps.get_db),
) -> dict:
    try:
        board = crud.board.delete(db=db, board_id=board_id)
        return board

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")
