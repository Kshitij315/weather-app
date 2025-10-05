# app/db.py
from sqlmodel import SQLModel, create_engine, Session
import os

# Database file placed in project root
DATABASE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "weather_history.db")
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
