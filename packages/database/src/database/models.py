from sqlalchemy import Column, Enum, String, DateTime, Boolean, Float, Integer
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


class BookEntry(Base):
    __tablename__ = "books"
    listingid = Column(String, primary_key=True)
    image_url = Column(String)
    image_file = Column(String)
    title = Column(String)
    magazine = Column(Boolean)
    set = Column(Boolean)
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
    batch_request_id = Column(
        String, doc="Identifier for the API batch request for the label."
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
