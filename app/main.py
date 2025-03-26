from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.exceptions import register_exception_handlers

app = FastAPI(title="Board API", openapi_url="/openapi.json")

register_exception_handlers(app)

app.mount("/front", StaticFiles(directory="front"), name="front")

@app.get("/", response_class=HTMLResponse)
def root():
    with open("front/index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")