import pytest
from sqlalchemy.orm import sessionmaker

from database.main import init_db, get_engine


@pytest.fixture
def temp_db():
    """Initialize the database and create a session"""
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)

    session = sessionmaker(bind=engine)
    session = session()

    yield session

    session.close()
