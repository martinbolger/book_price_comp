from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from book_scraper.models import ManifestEntry

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ManifestManager:
    def __init__(
        self,
        session: Session,
        expiration_days: int = 7,
        current_time: datetime = None,
    ):
        self.session = session
        self.expiration_days = expiration_days
        self.expiration_date = (current_time or datetime.now()) - timedelta(
            days=self.expiration_days
        )

    def url_covered(self, url: str) -> bool:
        """Checks if the URL is already in the manifest and is past the expiration date."""
        entry = (
            self.session.query(ManifestEntry).filter(ManifestEntry.url == url).first()
        )
        if entry and entry.last_read_date > self.expiration_date:
            return True
        return False

    def add_to_manifest(self, url: str, last_read_date: datetime = None) -> None:
        """Adds a URL and last read date to the manifest."""
        last_read_date = last_read_date or datetime.now()

        entry = (
            self.session.query(ManifestEntry).filter(ManifestEntry.url == url).first()
        )

        # Entry exists but is expired, update it
        if entry and not self.url_covered(url):
            logger.info(f"Updating existing entry for URL: {url}")
            entry.last_read_date = last_read_date
        # Entry does not exist, add new entry
        elif not entry:
            logger.info(f"Adding new entry for URL: {url}")
            self.session.add(ManifestEntry(url=url, last_read_date=last_read_date))

        self.session.commit()
