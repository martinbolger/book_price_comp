from sqlalchemy.orm import Session

from abc import ABC, abstractmethod

from database.models import RawBookoffListing, RawEbayListing


class RawListingManager(ABC):
    """Manages the raw eBay listing entries in the database, including adding new listings and updating existing ones."""

    def __init__(self, session: Session):
        """
        Initializes the RawListingManager with a database session.

        Parameters
        ----------
        session : Session
            SQLAlchemy session for database operations.
        """
        self.session = session

    def add_listings(self, listings: list[dict]) -> int:
        """
        Adds all listing entries that do not already exist to the database.

        Parameters
        ----------
        listings : list[dict]
            A list of dictionaries, each representing a listing to be added.

        Returns
        -------
        added_count : int
            The number of listings that were successfully added to the database.
        """
        added_count = 0
        for listing in listings:
            listing_added = self._add_listing(**listing)
            if listing_added:
                added_count += 1
        return added_count

    @abstractmethod
    def _add_listing(self, **kwargs) -> bool:
        """Adds a listing entry to the database."""
        raise NotImplementedError("Subclasses must implement this method.")

    def __enter__(self):
        """Context manager entry point for the RawListingManager class."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point for the RawListingManager class."""
        self.session.close()


class RawEbayListingManager(RawListingManager):
    """Manages the raw eBay listing entries in the database, including adding new listings and updating existing ones."""

    def _add_listing(self, listingid: str, **kwargs) -> bool:
        """
        Adds a listing entry to the database.

        Returns
        -------
        bool
            True if the listing was added, False if it already exists.
        """

        entry = (
            self.session.query(RawEbayListing)
            .filter(RawEbayListing.listingid == listingid)
            .first()
        )
        if entry:
            print(f"Listing already exists in database: {listingid}")
            return False

        self.session.add(
            RawEbayListing(
                listingid=listingid,
                **kwargs,
            )
        )
        self.session.commit()

        return True


class RawBookoffListingManager(RawListingManager):
    """Manages raw BookOff listings in the database."""

    def _add_listing(self, raw_item_id: str, **kwargs) -> bool:
        """
        Adds a BookOff listing entry to the database.

        Returns
        -------
        bool
            True if the listing was added, False if it already exists.
        """

        entry = (
            self.session.query(RawBookoffListing)
            .filter(RawBookoffListing.raw_item_id == raw_item_id)
            .first()
        )
        if entry:
            print(f"Listing already exists in database: {raw_item_id}")
            return False

        self.session.add(
            RawBookoffListing(
                raw_item_id=raw_item_id,
                **kwargs,
            )
        )
        self.session.commit()

        return True
