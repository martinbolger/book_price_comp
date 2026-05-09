from sqlalchemy.orm import sessionmaker
from pathlib import Path

# main.py (or your primary scraper script)
from book_scraper.database import init_db, get_engine
from book_scraper.ingestion.manager import ManifestManager
from book_scraper.run_injestion_cycle import Scraper
from book_scraper.seller_info import SellerInfo


def main(seller_info: list[SellerInfo], output_path: Path, expiration_days: int = 7):
    """
    Runs the scraping and ingestion cycle for a list of URLs, managing the manifest to avoid re-scraping recently scraped URLs.

    Parameters
    ----------
    urls : list[str]
        List of URLs to scrape.
    output_path : Path
        Path to save the scraped HTML output.
    expiration_days : int, optional
        Number of days after which a URL is considered expired and can be scraped again.
    """

    scraper = Scraper()

    # STEP 1: Ensure the database and tables exist
    engine = get_engine()
    init_db(engine)

    session = sessionmaker(bind=engine)
    session_local = session()

    # STEP 2: Open a communication session
    # Using 'with' ensures the session closes automatically when done
    with session_local as session:

        # STEP 3: Hand that session to your Manager
        manager = ManifestManager(session, expiration_days=expiration_days)

        # Get objects for sellers that are not covered by the manifest
        targets = [
            seller
            for seller in seller_info
            if not manager.seller_id_covered(seller.seller_id)
        ]

        # STEP 4: Run the scraper on the target URLs
        if targets:
            scraper.run(targets, output_path)

        # STEP 5
        for target in targets:
            manager.add_to_manifest(target.base_url)


if __name__ == "__main__":
    seller_names = [
        "jnts0710",
        "beyond_llc_jp01",
        "ninja_japan_shop",
        "yoshihiroshop",
        # "nkkt10-26",
        "japan-nihonbashi",
        # "romando",
    ]
    urls = []
    for seller_name in seller_names:
        sold_url = f"https://www.ebay.com/sch/i.html?_ex_kw=set%2C+magazine&_sacat=267&LH_Complete=1&LH_Sold=1&_fss=1&_saslop=1&_sasl=+{seller_name}&LH_SpecificSeller=1&_ipg=240"
        urls.append(sold_url)
    main(urls, output_path=Path(__file__).parent / "html_output")
