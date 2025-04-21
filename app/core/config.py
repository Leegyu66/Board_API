from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "secretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTE: int = 60
    TRITON_SERVER_URL: str = "triton-server:8001"

    class Config:
        case_sensitive = True

settings = Settings()