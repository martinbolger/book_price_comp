from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class ManifestEntry(Base):
    __tablename__ = "manifest"
    url = Column(String, primary_key=True)
    last_read_date = Column(DateTime, default=datetime.now)
