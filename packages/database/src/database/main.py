from email.mime import text
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Use an Environment Variable, but provide a default for local dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////var/task/debug/book_scraper.db")


def get_engine(url: str = DATABASE_URL):
    return create_engine(url)


def init_db(engine, drop_all=False):
    """Pass the engine explicitly so we can swap it during tests."""
    from .models import Base

    # Drop all tables only if you need to reset the database.
    if drop_all:
        Base.metadata.drop_all(engine)

    Base.metadata.create_all(engine)


def get_session(drop_all=False):
    """Set up a session for database operations. Pass drop_all=True to reset the database."""
    engine = get_engine()
    init_db(engine, drop_all=drop_all)
    return sessionmaker(bind=engine)()
