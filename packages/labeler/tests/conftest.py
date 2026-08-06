from labeler.batch_module import Label_Batch
import pytest
from unittest.mock import create_autospec


@pytest.fixture
def mock_client():
    """Creates a fake SDK client with predefined mock return values."""
    client = create_autospec(Label_Batch, instance=True)

    # Mock batch.create return object (needs a batch_id property)
    client.create_batch.return_value = "batch_xyz123"

    # Mock run_batch to just record calls
    client.run_batch.return_value = None

    client.model = "test_model"

    return client
