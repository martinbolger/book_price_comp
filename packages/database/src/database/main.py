import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from database.models import Base

# Load environment variables from .env
load_dotenv()

# Use an Environment Variable, but provide a default for local dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////var/task/debug/book_scraper.db")

def get_session(url: str|None = None):
    """Set up a session for database operations. Pass drop_all=True to reset the database."""
    if url is None:
        url = DATABASE_URL
    engine = create_engine(url=url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()



