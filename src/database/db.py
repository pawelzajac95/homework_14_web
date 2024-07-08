from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os
from sqlalchemy.sql.sqltypes import DateTime
from datetime import datetime
from sqlalchemy import *
from conf.config import settings


load_dotenv()


SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url



engine = create_engine(
    SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()