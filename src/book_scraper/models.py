from sqlalchemy import Column, String, DateTime, Boolean, Float
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class ManifestEntry(Base):
    __tablename__ = "manifest"
    url = Column(String, primary_key=True)
    last_read_date = Column(DateTime, default=datetime.now)


class BookEntry(Base):
    __tablename__ = "books"
    listingid = Column(String, primary_key=True)
    image_url = Column(String)
    image_file = Column(String)
    title = Column(String)
    magazine = Column(Boolean)
    sold_date = Column(DateTime)
    price_usd = Column(Float)
    shipping_cost = Column(Float)
    total_price = Column(Float)
    resolution_attempted = Column(Boolean, default=False)
    title_jp = Column(String)
    isbn = Column(String)
