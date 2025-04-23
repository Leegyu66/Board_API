from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.custom_exception import BadRequestError, Forbidden, NotFoundError, UnAuthorized, ServerError

async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )

async def bad_request_handler(request: Request, exc: BadRequestError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

async def forbidden_handler(request: Request, exc: Forbidden):
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc)}
    )

async def unauth_handler(request: Request, exc: UnAuthorized):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)}
    )

async def server_error_handler(request: Request, exc: ServerError):
    return JSONResponse(
        status=500,
        content={"detail": str(exc)}
    )