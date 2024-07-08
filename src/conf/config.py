from pydantic_settings import BaseSettings
from pydantic import ValidationError

class Settings(BaseSettings):
    sqlalchemy_database_url: str = 'postgresql+psycopg2://postgres:567234@localhost:5432/postgres'
    secret_key: str = 'secret'
    algorithm: str = 'HS256'
    mail_username: str = 'example@meta.ua'
    mail_password: str = 'password'
    mail_from: str = 'example@meta.ua'
    mail_port: int = 465
    mail_server: str = 'smtp.meta.ua'
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_password: str = 'password'
    cloudinary_name: str = 'None'
    cloudinary_api_key: str = 'None'
    cloudinary_api_secret: str = 'None'
    
settings = Settings()

try:
    Settings()
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


