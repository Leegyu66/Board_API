from fastapi import APIRouter
from app.api.endpoints import user, board

api_router = APIRouter()
api_router.include_router(user.api_router, prefix="/user", tags=["user"])
api_router.include_router(board.api_router, prefix="/board", tags=["board"])