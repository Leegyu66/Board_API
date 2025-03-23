from fastapi import FastAPI, APIRouter, HTTPException, Depends

from typing import List
from sqlalchemy.orm import Session

from app.schemas.board import Board, BoardCreate, BoardUpdate, BoardInDBBase
from app.schemas.user import UserCreate, UserInDBBase
from app import deps
from app import crud

from app.exceptions import value_error_handler

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import status


app = FastAPI(title="Recipe API", openapi_url="/openapi.json")

api_router = APIRouter()


@api_router.get("/", status_code=200)
def root() -> dict:
    return {"title": "게시판 API"}

# 게시판 읽기 - 1
@api_router.get("/board", status_code=200)
def read_board(
    db: Session = Depends(deps.get_db),
) -> List:
    
    lists = crud.board.get_multi(db)
    return lists

# 게시판 읽기 - 2
@api_router.get("/board/{board_id}", status_code=200, response_model=BoardInDBBase)
def fetch_board(
    board_id: int,
    db: Session = Depends(deps.get_db),
) -> dict:
    
    result = crud.board.get(db=db, id=board_id)
    return result


# 게시판 읽기 3
@api_router.get("/board/user/{user_id}", status_code=200, response_model=List[BoardInDBBase])
def get_user_posts(
    user_id: int,
    db: Session = Depends(deps.get_db),
) -> dict:
    
    boards = crud.board.get_user_posts(db=db, user_id=user_id)
    return boards

# 게시판 쓰기
@api_router.post("/board/", status_code=201, response_model=Board)
def create_board(
    board_in: BoardCreate,
    db: Session = Depends(deps.get_db)
) -> dict:
    
    board = crud.board.create_board(db=db, board_in=board_in)
    return board
    
# 게시판 수정
@api_router.patch("/board/{board_id}", status_code=200, response_model=Board)
def update_board(
    board_id: int,
    board_in: BoardUpdate,
    db: Session = Depends(deps.get_db),
) -> dict:
    
    board = crud.board.update_board(db=db, board_id=board_id, board_update=board_in)
    return board


# 게시판 삭제
@api_router.delete("/board/{board_id}", status_code=200, response_model=Board)
def delete_board(
    board_id: int,
    db: Session = Depends(deps.get_db),
) -> dict:
    
    board = crud.board.delete(db=db, board_id=board_id)
    return board


@api_router.delete("/board/{board_id}/hard", status_code=200, response_model=dict)
def delete_board_hard(
    board_id: int,
    db: Session = Depends(deps.get_db),
) -> dict:
    
    board = crud.board.delete_hard(db=db, board_id=board_id)
    return board


@api_router.post("/user", status_code=201, response_model=UserCreate)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> dict:
    
    user = crud.user.create(db=db, user_in=user_in)
    return user

@api_router.post("/user/login", status_code=200)
def login(
    login_form: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(deps.get_db),
) -> dict:
    
    user = crud.user.get_by_email(db, login_form.username)

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user or password")
    
    res = crud.user.verify_password(login_form.password, user.password)

    if not res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user or password")
    
    return {"message": "Login successful", "user_id": user.id}


app.add_exception_handler(ValueError, value_error_handler)
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")
