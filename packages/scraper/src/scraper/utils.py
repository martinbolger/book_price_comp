import hashlib


def hash_string(string: str, hash_length: int = 13) -> str:
    """Hashes a string using SHA-256 and returns the first `hash_length` characters of the hex digest."""
    return hashlib.sha256(string.encode("utf-8")).hexdigest()[:hash_length]
