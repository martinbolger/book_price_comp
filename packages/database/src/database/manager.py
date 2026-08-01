from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database.models import BookEntry, ManifestEntry, LabelEntry

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

    def seller_id_covered(self, seller_id: str, entry: ManifestEntry = None) -> bool:
        """Checks if the seller ID is already in the manifest and is past the expiration date."""
        if not entry:
            entry = (
                self.session.query(ManifestEntry)
                .filter(ManifestEntry.seller_id == seller_id)
                .first()
            )
        if entry and entry.last_read_date > self.expiration_date:
            return True
        return False

    def add_to_manifest(self, seller_id: str, last_read_date: datetime = None) -> None:
        """Adds a seller_id and last read date to the manifest."""
        last_read_date = last_read_date or datetime.now()

        entry = (
            self.session.query(ManifestEntry)
            .filter(ManifestEntry.seller_id == seller_id)
            .first()
        )

        # If covered and not expired, do nothing
        if self.seller_id_covered(seller_id, entry):
            logger.info(f"seller_id already covered and not expired: {seller_id}")
            return

        # Entry exists but is expired, update it
        if entry:
            logger.info(f"Updating existing entry for seller_id: {seller_id}")
            entry.last_read_date = last_read_date
        # Entry does not exist, add new entry
        else:
            logger.info(f"Adding new entry for seller_id: {seller_id}")
            self.session.add(
                ManifestEntry(seller_id=seller_id, last_read_date=last_read_date)
            )

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

    def add_seller_id(self, listingid: str, seller_id: str):
        """Add seller id to the data for a book with a given listing ID if one does not already exist."""
        entry = (
            self.session.query(BookEntry)
            .filter(BookEntry.listingid == listingid)
            .first()
        )
        if entry and entry.seller_id is None:
            entry.seller_id = seller_id
            self.session.commit()

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

    def add_image_file(self, image_url: str, image_file: str) -> None:
        """Adds a local image file path to a book entry based on the image URL."""
        entries = (
            self.session.query(BookEntry).filter(BookEntry.image_url == image_url).all()
        )
        if entries:
            for entry in entries:
                entry.image_file = image_file
            self.session.commit()

    def add_book(self, listingid: str, title: str, **kwargs) -> bool:
        """
        Adds a book entry to the database.

        Returns
        -------
        bool
            True if the book was added, False if it already exists.
        """

        entry = (
            self.session.query(BookEntry)
            .filter(BookEntry.listingid == listingid)
            .first()
        )
        if entry:
            logger.info(f"Exact book already exists in database: {listingid}, {title}")
            return False

        # Implement logic to add book to the database
        self.session.add(
            BookEntry(
                listingid=listingid,
                title=title,
                **kwargs,
            )
        )
        self.session.commit()

        return True


class LabelManager:
    """Manages the label entry table in the database including adding a new entry for a pending label and updating the status when a label is generated."""

    def __init__(self, session: Session):
        """
        Initializes the LabelManager with a database session.

        Parameters
        ----------
        session : Session
            SQLAlchemy session for database operations.
        """
        self.session = session

    def add_new_url(
        self, image_url: str, model_used: str, batch_request_id: str
    ) -> None:
        """Adds a new image url entry to the database with a pending status."""
        self.session.add(
            LabelEntry(
                image_url=image_url,
                model_used=model_used,
                status="pending",
                batch_request_id=batch_request_id,
            )
        )
        self.session.commit()

    def update_url_label(self, image_url: str, model_used: str, label: str) -> None:
        """Updates the label entry in the database with the generated label and marks it as completed."""
        entry = (
            self.session.query(LabelEntry)
            .filter(
                LabelEntry.image_url == image_url, LabelEntry.model_used == model_used
            )
            .first()
        )
        if entry:
            entry.label = label
            entry.status = "completed"
            self.session.commit()

    def update_urls_to_failed(self):
        """Updates all pending label entries that are more than 24 hours old to failed status."""
        expiration_time = datetime.timezone.utc.now() - timedelta(hours=24)
        entries = (
            self.session.query(LabelEntry)
            .filter(
                LabelEntry.status == "pending", LabelEntry.created_at < expiration_time
            )
            .all()
        )
        for entry in entries:
            entry.status = "failed"
        self.session.commit()
