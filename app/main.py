from fastapi import FastAPI
from app.exceptions import value_error_handler
from app.api import api_router

app = FastAPI(title="Board API", openapi_url="/openapi.json")


@api_router.get("/", status_code=200)
def root() -> dict:
    return {"title": "게시판 API"}


app.add_exception_handler(ValueError, value_error_handler)
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")
