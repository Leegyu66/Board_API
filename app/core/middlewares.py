from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://192.168.100.145:8080",
]

def add_middleware(app: FastAPI) -> None:

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    