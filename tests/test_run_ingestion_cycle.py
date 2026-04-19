from book_scraper.run_injestion_cycle import Scraper


class TestScraper:
    def test_run(self, tmp_path):
        # Given
        scraper = Scraper()
        urls = ["https://example.com/page1", "https://example.com/page2"]

        # When
        scraper.run(urls, output_path=tmp_path)

        # Then
        for url in urls:
            url_hash = scraper.hash_string(url)
            output_file = tmp_path / f"{url_hash}.html"
            assert output_file.exists()
