import requests
from sqlalchemy.orm import sessionmaker
import time
from pathlib import Path
import logging
import random

from database.database import get_engine, init_db
from database.models import BookEntry
from database.manager import BookManager
from scraper.utils import hash_string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_images(base_path: Path):
    # STEP 1: Ensure the database and tables exist
    engine = get_engine()
    init_db(engine)

    session = sessionmaker(bind=engine)
    session_local = session()

    with session_local as session:
        for i, book in enumerate(session.query(BookEntry).all()):
            image_filename = f"{hash_string(book.image_url)}.webp"
            image_path = base_path / "images" / f"{hash_string(book.image_url)}.webp"
            # Skip if image already downloaded
            if image_path.exists():
                logging.info(
                    f"Image already exists for listing {book.listingid}, skipping download."
                )
                continue
            logging.info(
                f"Downloading image for listing {book.title} from {book.image_url}"
            )
            image_url = book.image_url
            image_bytes = requests.get(image_url).content
            # Add a short delay to avoid overwhelming the server
            time.sleep(random.uniform(0, 0.4))
            # Save the image to the local filesystem
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            # Update the database entry with the local image file path
            book_manager = BookManager(session)
            book_manager.add_image_file(
                image_url=book.image_url, image_file=str(image_filename)
            )
            # if i > 100:
            # break  # Limit to first 100 images for testing purposes


if __name__ == "__main__":
    base_path = Path(__file__).parent
    (base_path / "images").mkdir(exist_ok=True)
    download_images(base_path)
