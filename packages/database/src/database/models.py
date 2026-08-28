from sqlalchemy import Column, Enum, String, DateTime, Boolean, Float, JSON, func
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


class ManifestEntry(Base):
    __tablename__ = "manifest"
    seller_id = Column(String, primary_key=True)
    url = Column(String)
    # Use a lambda function to ensure the timestamp is generated at runtime, not import time.
    last_read_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RawEbayListing(Base):
    __tablename__ = "raw_ebay_listings"

    seller_id = Column(String, nullable=False)
    listingid = Column(String, primary_key=True)
    raw_title = Column(String, nullable=True)
    raw_price = Column(String, nullable=True)
    raw_sold_date = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    raw_attributes = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RawBookoffListing(Base):
    __tablename__ = "raw_bookoff_listings"

    search_term = Column(String, nullable=False)
    raw_item_id = Column(String, primary_key=True)
    raw_rel_url = Column(String, nullable=True)
    raw_title = Column(String, nullable=True)
    raw_author = Column(String, nullable=True)
    raw_price = Column(String, nullable=True)
    raw_date = Column(String, nullable=True)
    raw_item_genre = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BookEntry(Base):
    __tablename__ = "books"
    listingid = Column(String, primary_key=True)
    image_url = Column(String)
    image_file = Column(String)
    title = Column(String)
    magazine = Column(
        Boolean,
        doc="Indicates if the book is a magazine.",
        nullable=False,
        default=False,
        server_default="false",
    )
    set = Column(
        Boolean,
        doc="Indicates if the book is part of a set.",
        nullable=False,
        default=False,
        server_default="false",
    )
    sold_date = Column(DateTime)
    price_usd = Column(Float)
    shipping_cost = Column(Float)
    total_price = Column(Float)
    seller_id = Column(String)


class LabelEntry(Base):
    __tablename__ = "labels"
    image_url = Column(String, doc="URL of the image.", primary_key=True)
    model_used = Column(
        String, doc="The model used to generate the label.", primary_key=True
    )
    batch_id = Column(
        String, doc="Identifier for the API batch request that the label as a part of."
    )
    batch_request_id = Column(
        String, doc="Identifier for the individual request for the label."
    )
    status = Column(
        Enum("pending", "completed", "failed", name="status_enum"),
        default="pending",
        doc="Indicates if the labeling process is pending, completed, or failed.",
    )
    # Use a lambda function to ensure the timestamp is generated at runtime, not import time.
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        doc="Timestamp when the batch request for the label was queued.",
    )
    # Use a lambda function to ensure the timestamp is generated at runtime, not import time.
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        doc="Timestamp when the entry was last updated.",
    )
    label = Column(String, doc="The label assigned to the image.")
