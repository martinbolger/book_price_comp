from abc import ABC, abstractmethod

from bs4 import Tag


class ScraperStrategy(ABC):
    @property
    @abstractmethod
    def current_url(self) -> str:
        """Returns the current URL."""
        raise NotImplementedError

    @abstractmethod
    def parse(self, html: str, **kwargs):
        """Parses the HTML and returns a dictionary of extracted data."""
        raise NotImplementedError

    @abstractmethod
    def should_continue(self, **kwargs) -> bool:
        """Returns True if the scraper should continue, or False when done."""
        raise NotImplementedError

    @staticmethod
    def _get_text(item: Tag, selector: str) -> str | None:
        """Extract stripped text from a CSS selector within an item node."""
        node = item.select_one(selector)
        return node.get_text(strip=True) if node else None
