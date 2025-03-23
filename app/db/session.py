from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URI = "mariadb+pymysql://choi:1234@mariadb:3306/board_api"

engine = create_engine(DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)