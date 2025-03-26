from fastapi import FastAPI
from app.exceptions.exception_handler import (
    not_found_handler,
    bad_request_handler,
    forbidden_handler,
    unauth_handler
)
from app.exceptions.custom_exception import (
    NotFoundError,
    BadRequestError,
    Forbidden,
    UnAuthorized
)

def register_exception_handlers(app: FastAPI) -> None:

    app.add_exception_handler(NotFoundError, not_found_handler)
    app.add_exception_handler(BadRequestError, bad_request_handler)
    app.add_exception_handler(Forbidden, forbidden_handler)
    app.add_exception_handler(UnAuthorized, unauth_handler)