from datetime import time

from sqlalchemy.orm import sessionmaker
from google import genai
import os

# main.py (or your primary scraper script)
from book_scraper.database import init_db, get_engine
from book_scraper.ingestion.manager import BookManager
from book_scraper.resolve_titles.book_title_gem import (
    identify_book,
    identify_book_local,
)


def main():

    # client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    # STEP 1: Ensure the database and tables exist
    engine = get_engine("sqlite:///books.db")  # or your actual database URL
    init_db(engine)

    session = sessionmaker(bind=engine)
    session_local = session()

    # STEP 2: Open a communication session
    # Using 'with' ensures the session closes automatically when done
    with session_local as session:

        # STEP 3: Hand that session to your Manager
        manager = BookManager(session)

        entries = manager.missing_jp_title()

        # Resolve titles for entries missing Japanese titles
        for index, entry in enumerate(entries):
            if entry.magazine:
                continue
            try:
                resolved_title_jp = identify_book_local(entry.image_url)
                if resolved_title_jp:
                    manager.add_jp_title(entry.image_url, resolved_title_jp)

                # Add a short sleep to avoid hitting API rate limits
                time.sleep(5)

                if (index + 1) % 10 == 0:
                    print(f"Processed {index + 1} entries, sleeping for 5 seconds...")
                    time.sleep(5)

            except:
                manager.add_failed_resolution(entry.image_url)


if __name__ == "__main__":
    main()
