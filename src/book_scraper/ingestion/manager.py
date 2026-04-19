from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from book_scraper.models import BookEntry, ManifestEntry

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ManifestManager:
    """Manages the manifest of URLs that have been scraped, including expiration logic."""

    def __init__(
        self,
        session: Session,
        expiration_days: int = 7,
        current_time: datetime = None,
    ):
        """
        Initializes the ManifestManager with a database session and expiration settings.

        Parameters
        ----------
        session : Session
            SQLAlchemy session for database operations.
        expiration_days : int, optional
            Number of days after which a URL is considered expired (default is 7).
        current_time : datetime, optional
            Current time for calculating expiration (default is None, which uses datetime.now()).
        """
        self.session = session
        self.expiration_days = expiration_days
        self.expiration_date = (current_time or datetime.now()) - timedelta(
            days=self.expiration_days
        )

    def url_covered(self, url: str, entry: ManifestEntry = None) -> bool:
        """Checks if the URL is already in the manifest and is past the expiration date."""
        if not entry:
            entry = (
                self.session.query(ManifestEntry)
                .filter(ManifestEntry.url == url)
                .first()
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

        # If covered and not expired, do nothing
        if self.url_covered(url, entry):
            logger.info(f"URL already covered and not expired: {url}")
            return

        # Entry exists but is expired, update it
        if entry:
            logger.info(f"Updating existing entry for URL: {url}")
            entry.last_read_date = last_read_date
        # Entry does not exist, add new entry
        else:
            logger.info(f"Adding new entry for URL: {url}")
            self.session.add(ManifestEntry(url=url, last_read_date=last_read_date))

        self.session.commit()


class BookManager:
    """Manages book entries in the database, including adding new books and resolving missing Japanese titles."""

    def __init__(self, session: Session):
        """
        Initializes the BookManager with a database session.

        Parameters
        ----------
        session : Session
            SQLAlchemy session for database operations.
        """
        self.session = session

    def missing_jp_title(self) -> bool:
        """Returns a list of book entries that are missing a Japanese title and have not yet been attempted for resolution."""
        entries = (
            self.session.query(BookEntry)
            .filter(BookEntry.title_jp == None, BookEntry.resolution_attempted == False)
            .all()
        )
        return entries

    def add_failed_resolution(self, image_url: str) -> None:
        """Marks a book entry as having attempted resolution without success."""
        entry = (
            self.session.query(BookEntry)
            .filter(BookEntry.image_url == image_url)
            .first()
        )
        if entry:
            entry.resolution_attempted = True
            self.session.commit()

    def add_jp_title(self, image_url: str, title_jp: str) -> None:
        """Adds a Japanese title to a book entry based on the image URL."""
        entries = (
            self.session.query(BookEntry).filter(BookEntry.image_url == image_url).all()
        )
        if entries:
            for entry in entries:
                entry.title_jp = title_jp
                entry.resolution_attempted = True
            self.session.commit()

    def add_book(
        self,
        listingid: str,
        title: str,
        magazine: bool,
        sold_date: datetime,
        image_url: str,
        price_usd: float,
        shipping_cost: float,
        total_price: float,
    ) -> None:
        """Adds a book entry to the database."""

        entry = (
            self.session.query(BookEntry)
            .filter(BookEntry.listingid == listingid)
            .first()
        )
        if entry:
            logger.info(
                f"Exact book already exists in database: {listingid}, {title}, {sold_date}"
            )
            return

        # Implement logic to add book to the database
        self.session.add(
            BookEntry(
                listingid=listingid,
                title=title,
                magazine=magazine,
                sold_date=sold_date,
                image_url=image_url,
                price_usd=price_usd,
                shipping_cost=shipping_cost,
                total_price=total_price,
                resolution_attempted=False,
            )
        )
        self.session.commit()
