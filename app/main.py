from fastapi import FastAPI

from app.api import api_router
from app.exceptions import register_exception_handlers

app = FastAPI(title="Board API", openapi_url="/openapi.json")

register_exception_handlers(app)

@api_router.get("/", status_code=200)
def root() -> dict:
    return {"title": "게시판 API"}


app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")