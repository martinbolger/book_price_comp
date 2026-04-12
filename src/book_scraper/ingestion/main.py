from sqlalchemy.orm import sessionmaker
from pathlib import Path

# main.py (or your primary scraper script)
from book_scraper.database import init_db, get_engine
from book_scraper.ingestion.manager import ManifestManager
from book_scraper.run_injestion_cycle import Scraper


def main(urls: list[str], output_path: Path, expiration_days: int = 7):

    scraper = Scraper()

    # STEP 1: Ensure the database and tables exist
    engine = get_engine("sqlite:///manifest.db")  # or your actual database URL
    init_db(engine)

    session = sessionmaker(bind=engine)
    session_local = session()

    # STEP 2: Open a communication session
    # Using 'with' ensures the session closes automatically when done
    with session_local as session:

        # STEP 3: Hand that session to your Manager
        manager = ManifestManager(session, expiration_days=expiration_days)

        target_urls = [url for url in urls if not manager.url_covered(url)]

        # STEP 4: Run the scraper on the target URLs
        if target_urls:
            scraper.run(target_urls, output_path)

        # STEP 5
        for url in target_urls:
            manager.add_to_manifest(url)


if __name__ == "__main__":
    seller_names = [
        "jnts0710",
        "beyond_llc_jp01",
        "ninja_japan_shop",
        "yoshihiroshop",
        "nkkt10-26",
    ]
    urls = []
    for seller_name in seller_names:
        sold_url = f"https://www.ebay.com/sch/i.html?_ex_kw=set%2C+magazine&_sacat=267&LH_Complete=1&LH_Sold=1&_fss=1&_saslop=1&_sasl=+{seller_name}&LH_SpecificSeller=1&_ipg=240"
        urls.append(sold_url)
    main(urls, output_path=Path(__file__).parent / "html_output")
