import pytest
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from book_scraper.ingestion.manager import ManifestManager
from book_scraper.models import ManifestEntry
from book_scraper.database import init_db, get_engine


@pytest.fixture
def temp_db():
    # Initialize the database and create a session
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)

    session = sessionmaker(bind=engine)
    session = session()

    yield session

    session.close()


class TestManifestManager:
    def test_url_covered(self, temp_db):
        manager = ManifestManager(temp_db, expiration_days=7)
        url = "https://example.com"

        # URL not covered
        assert not manager.url_covered(url)
        # Add URL to manifest
        manager.add_to_manifest(url)
        # URL is covered
        assert manager.url_covered(url)

    def test_add_to_manifest(self, temp_db):
        current_time = datetime(2024, 5, 15, 10, 30)
        manager = ManifestManager(temp_db, expiration_days=7, current_time=current_time)
        url = "https://example.com"

        # Add URL to manifest
        manager.add_to_manifest(url, last_read_date=current_time)

        # Check if URL is in manifest
        entry = temp_db.query(ManifestEntry).filter(ManifestEntry.url == url).first()
        assert entry is not None
        assert entry.url == url

        # Try to add the same URL again with the same date (should not update)
        manager.add_to_manifest(url, last_read_date=current_time)

        # Check if URL is still in manifest and not duplicated
        entries = temp_db.query(ManifestEntry).filter(ManifestEntry.url == url).all()
        assert len(entries) == 1

    def test_url_not_covered_expired(self, temp_db):
        manager = ManifestManager(temp_db, expiration_days=1)
        url = "https://example.com"

        # Set expired date
        expired_date = datetime.now() - timedelta(days=10)

        # Add URL with expired date
        manager.add_to_manifest(url, last_read_date=expired_date)

        # URL should not be covered
        assert not manager.url_covered(url)

        # Update URL with current date
        manager.add_to_manifest(url, last_read_date=datetime.now())

        # URL should now be covered
        assert manager.url_covered(url)
