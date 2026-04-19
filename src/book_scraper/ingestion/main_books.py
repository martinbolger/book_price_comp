from sqlalchemy.orm import sessionmaker
from pathlib import Path

# main.py (or your primary scraper script)
from book_scraper.database import init_db, get_engine
from book_scraper.ingestion.manager import BookManager
from book_scraper.ingestion.ebay import parse_html


def main(html_path: Path, parser: callable = parse_html):
    """Runs the parsing and database update cycle for a directory of HTML files containing book data.

    Parameters
    ----------
    html_path : Path
        Path to the directory containing HTML files.
    parser : callable, optional
        Parser function to extract book data from HTML content (default is parse_html).
    """
    # STEP 1: Parse HTML files to extract book data
    books = parse_html_files(html_path, parser=parser)

    # STEP 2: Update the database with the extracted book data
    update_db(books)


def parse_html_files(html_path: Path, parser: callable):
    """Parses all HTML files in the given directory using the provided parser function."""
    books = []
    for html_file in html_path.glob("*.html"):
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        books.extend(parser(html_content))
    return books


def update_db(books: list[dict]):
    # STEP 1: Ensure the database and tables exist
    engine = get_engine("sqlite:///books.db")
    init_db(engine)

    session = sessionmaker(bind=engine)
    session_local = session()

    # STEP 2: Open a communication session
    # Using 'with' ensures the session closes automatically when done
    with session_local as session:

        # STEP 3: Hand that session to your Manager
        book_manager = BookManager(session)

        # STEP 4: Add books to the database
        for book in books:
            book_manager.add_book(
                listingid=book["listingid"],
                title=book["title"],
                magazine=book["magazine"],
                sold_date=book["sold_date"],
                image_url=book["image_url"],
                price_usd=book["price_usd"],
                shipping_cost=book["shipping_cost"],
                total_price=book["total_price"],
            )


if __name__ == "__main__":
    html_path = Path(__file__).parent / "html_output"
    main(html_path)
