import logging
from scraper.browser_managerment import PlaywrightFetcher

logger = logging.getLogger(__name__)


def orchestrate_pagination(
    fetcher: PlaywrightFetcher,
    parser: callable,
    start_url: str,
    db_writer: callable,
    next_url_fn: callable,
):
    current_url = start_url
    page_num = 1

    while current_url is not None:
        print(f"Scraping page {page_num}: {current_url}")

        records = process_one_page(fetcher, parser, db_writer, current_url)
        if records is None:
            break

        current_url = next_url_fn(current_url, page_num, records)
        page_num += 1


def process_one_page(
    fetcher: PlaywrightFetcher,
    html_parser: callable,
    db_writer: callable,
    url: str = None,
):
    """Orchestrates fetching, parsing, and database saving."""
    html = fetcher.fetch_html(url)
    parsed_html = html_parser(html, url)
    db_writer(parsed_html)
    return parsed_html
