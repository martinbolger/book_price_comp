import os
from sqlalchemy import create_engine

# 1. Use an Environment Variable, but provide a default for local dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///book_scraper.db")


def get_engine(url=DATABASE_URL):
    return create_engine(url)


def init_db(engine):
    """Pass the engine explicitly so we can swap it during tests."""
    from .models import Base

    Base.metadata.create_all(engine)
