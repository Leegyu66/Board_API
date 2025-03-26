from fastapi import Depends, Request
from jose import JWTError, jwt
from app import crud
from app.exceptions.custom_exception import UnAuthorized
from app.models.user import User
from app.core import settings
from app.deps import get_db
from sqlalchemy.orm import Session

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")

    if not token:
        raise UnAuthorized("Not authenticated")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email_or_name = payload.get("sub")
        if email_or_name is None:
            raise UnAuthorized("Invalid token")
    except JWTError:
        raise UnAuthorized("Invalid token")

    user = crud.user.get_by_email(db, email_or_name)
    if user is None:
        raise UnAuthorized("User not found")

    return user