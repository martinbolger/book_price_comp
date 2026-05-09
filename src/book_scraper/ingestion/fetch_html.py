import pandas as pd
from pathlib import Path

from book_scraper.database import SessionLocal
from book_scraper.models import ManifestEntry


class URLManifest:
    def __init__(self, manifest_csv: Path, expiration_days: int = 7):
        self.manifest_csv = manifest_csv
        self.pending_urls = []
        self._manifest = None
        self.expiration_days = expiration_days

    @property
    def manifest(self) -> pd.DataFrame:
        """Loads the manifest CSV file into a dataframe."""
        if self._manifest is None:
            if Path(self.manifest_csv).exists():
                self._manifest = pd.read_csv(self.manifest_csv)
            else:
                self._manifest = pd.DataFrame(columns=["url", "last_read_date"])
                self._manifest.set_index("url", inplace=True)
        return self._manifest

    def append_url(self, url: str) -> None:
        """Appends url and last read date to manifest if it is not already covered."""
        if not self.url_covered(url):
            self.pending_urls.append(url)

    def url_covered(self, url: str) -> bool:
        """Checks if the URL is already in the manifest and is past the expiration date."""
        # If url is in pending updates, it is covered
        if any(update_url == url for update_url in self.pending_urls):
            return True
        # If url is in manifest and last read date is within expiration days, it is covered
        expiration_date = pd.Timestamp.now() - pd.Timedelta(days=self.expiration_days)
        if (
            url in self.manifest.index
            and self.manifest.loc[url, "last_read_date"].values[0] > expiration_date
        ):
            return True
        return False

    def add_to_manifest(self, url: str, last_read_date: pd.Timestamp) -> None:
        """Adds a URL and last read date to the manifest dataframe."""
        self._manifest = pd.concat(
            [
                self.manifest,
                pd.DataFrame([{"last_read_date": last_read_date}], index=[url]),
            ],
            ignore_index=False,
        )

    def save_manifest(self) -> None:
        """Saves the manifest dataframe to CSV."""

        self._manifest = pd.concat(
            [
                self._manifest,
                pd.DataFrame(
                    [{"last_read_date": pd.Timestamp.now()}],
                    index=[self.pending_urls],
                ),
            ],
            ignore_index=False,
        )
        self.manifest.to_csv(self._manifest, index=True)
        self.pending_urls = []


if __name__ == "__main__":
    seller_name = "example_seller"
    sold_url = f"https://www.ebay.com/sch/i.html?_ex_kw=set%2C+magazine&_sacat=267&LH_Complete=1&LH_Sold=1&_fss=1&_saslop=1&_sasl=+{seller_name}&LH_SpecificSeller=1&_ipg=240"
    data_dir = Path(__file__).parent.parent.parent / "data"
    html = orchestrate(sold_url, data_dir)
