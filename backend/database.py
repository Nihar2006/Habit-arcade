<<<<<<< HEAD
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Ensure consistent absolute DB file location regardless of server execution CWD
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "retro_tracker.db"

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

# Handle legacy Heroku/Render postgres:// prefix
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure engine connect args for SQLite
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)
=======
"""
database.py
------------
SQLite engine + session factory for the Retro Arcade Habit Tracker.
The DB file (habit_arcade.db) is created automatically on first run,
right next to this file.
"""

import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./retro_tracker.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# check_same_thread=False is required for SQLite when used with FastAPI's
# threaded request handling (each request may run on a different thread).
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
>>>>>>> 506a17743a288bb23a716cf93d4e6e6edcd8f4f7

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

<<<<<<< HEAD
def get_db():
=======

def ensure_schema() -> None:
    """Create tables and add any missing auth columns for existing SQLite DBs."""
    Base.metadata.create_all(bind=engine)

    if not inspect(engine).has_table("users"):
        return

    with engine.begin() as conn:
        columns = {column["name"] for column in inspect(engine).get_columns("users")}
        if "username" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR"))
        if "email" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR"))
        if "password_hash" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR DEFAULT ''"))
        if "xp" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN xp INTEGER DEFAULT 0"))
        if "level" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1"))
        if "coins" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 100"))


ensure_schema()


def get_db():
    """FastAPI dependency: yields a DB session per-request and always closes it."""
>>>>>>> 506a17743a288bb23a716cf93d4e6e6edcd8f4f7
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
