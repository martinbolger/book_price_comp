from scraper.browser_managerment import PlaywrightFetcherSync


def save_ebay_session():
    with PlaywrightFetcherSync(headless=False) as fetcher:

        fetcher.fetch_html("https://www.ebay.com/signin")
        print(
            "Please log in manually in the browser window, then press ENTER in terminal..."
        )
        input()

        # Save your logged-in browser state to a JSON file
        fetcher.page.context.storage_state(path="ebay_state.json")

if __name__ == "__main__":
    save_ebay_session()