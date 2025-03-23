import logging


from app.db.base import Base
from app.db.session import engine
from app.db.init_db import init_db
from app.db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init():
    db = SessionLocal()
    Base.metadata.create_all(bind=engine)
    init_db(db)

def main():
    logger.info("create")
    init()
    logger.info("init")

if __name__=="__main__":
    main()