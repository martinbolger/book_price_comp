import pytest
from sqlalchemy.orm import sessionmaker
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from database.models import Base

from database.main import get_session


@pytest.fixture
def temp_db():
    """Initialize the database and create a session"""
    session = get_session("sqlite:///:memory:")
    yield session

    session.close()


@pytest.fixture
def temp_postgres_db():
    db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://mbolger:password123@db:5432/postgres",
    )

    admin_engine = create_engine(db_url, isolation_level="AUTOCOMMIT")
    db_name = "test_book_scraper_tmp"

    with admin_engine.begin() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
        conn.execute(text(f"CREATE DATABASE {db_name}"))

    engine = create_engine(
        f"postgresql://mbolger:password123@db:5432/{db_name}"
    )
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
        with admin_engine.begin() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))