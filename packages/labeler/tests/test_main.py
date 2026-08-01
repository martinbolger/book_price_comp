from freezegun import freeze_time
import pytest

from labeler.main import create_batch_name, add_images_to_batch


@freeze_time("2026-01-01 12:00:00")
def test_create_batch_name_format():
    """Verify batch name contains seller ID and expected timestamp format."""
    name = create_batch_name("seller_42")
    assert name.startswith("seller_42_")
    # Length check for seller_42_YYYYMMDD_HHMMSS
    assert len(name) == len("seller_42_20260101_120000")
