import hashlib
import pandas as pd
from pathlib import Path


class URLHashing:
    def __init__(self, manifest_csv: str):
        self.manifest_csv = manifest_csv

    @property
    def manifest(self) -> pd.DataFrame:
        """Loads the manifest CSV file into a dataframe."""
        manifest = (
            pd.read_csv(self.manifest_csv)
            if Path(self.manifest_csv).exists()
            else pd.DataFrame(columns=["filename", "url"])
        )
        return manifest

    def url_in_manifest(self, url: str) -> bool:
        """Checks if the URL is already in the manifest."""
        existing_entry = self.manifest[self.manifest["url"] == url]
        if not existing_entry.empty:
            return True
        else:
            return False

    def hash_in_manifest(self, hash: str) -> bool:
        """Checks if the hash is already in the manifest."""
        existing_entry = self.manifest[self.manifest["filename"] == hash]
        if not existing_entry.empty:
            return True
        else:
            return False

    def get_hash_for_url(self, url: str) -> str:
        """Gets the hash for a given URL, checking for collisions in the manifest."""
        hash = self.hash_string(url)
        while self.hash_in_manifest(hash):
            existing_entry = self.manifest[self.manifest["filename"] == hash]
            if not existing_entry.empty:
                if existing_entry.iloc[0]["url"] == url:
                    return hash
                else:
                    hash = self.hash_string(url, hash_length=len(hash) + 1)
        return hash

    @staticmethod
    def hash_string(string: str, hash_length: int = 13) -> str:
        """Hashes a string using SHA-256 and returns the first `hash_length` characters of the hex digest."""
        return hashlib.sha256(string.encode("utf-8")).hexdigest()[:hash_length]

    def write_url_to_manifest(self, url: str, filename: str, csv_file: str) -> str:
        """Writes the url and filename to the manifest CSV file."""
        self.manifest.concat([filename, url], ignore_index=True).to_csv(
            csv_file, index=False
        )


# Conver url to hash.
# If hash is already in the manifest, confirm the url matches the hash.
# If it doesn't, add a digit to the hash and check again until we find a match or an empty slot.
# If it does, we already have the HTML.
