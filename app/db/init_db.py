import logging
from sqlalchemy.orm import Session

import crud, schemas

logger = logging.getLogger(__name__)

FIRST_SUPERUSER = "adobe9938@gmail.com"

def init_db(db: Session) -> None:
    if FIRST_SUPERUSER:
        user = crud.user.get_by_email(db, email=FIRST_SUPERUSER)
        if not user:
            user_in = schemas.UserCreate(
                name="Kyuyoung",
                email=FIRST_SUPERUSER,
                login_id="adobe9938",
                password="1234",
                is_superuser=True
            )
            user = crud.user.create(db, obj_in=user_in)
        else:
            logger.warning(
                "exist"
            )
    
    else:
        logger.warning(
            "This is not superuser"
        )