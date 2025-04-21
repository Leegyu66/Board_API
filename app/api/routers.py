from fastapi import APIRouter
from app.api.endpoints import user, board, sr

api_router = APIRouter()
api_router.include_router(user.api_router, prefix="/user", tags=["user"])
api_router.include_router(board.api_router, prefix="/board", tags=["board"])
api_router.include_router(sr.api_router, prefix="/v1", tags=["sr"])