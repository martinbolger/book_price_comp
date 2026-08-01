from unittest.mock import MagicMock, call
import pytest

# Assuming your code is saved in `batch_module.py`
from labeler.batch_module import Batch


@pytest.fixture
def mock_client():
    """Creates a fake SDK client with predefined mock return values."""
    client = MagicMock()

    # Mock batch.create return object (needs a batch_id property)
    mock_batch = MagicMock()
    mock_batch.batch_id = "batch_abc123"
    client.batch.create.return_value = mock_batch

    # Mock chat.create return object
    mock_chat = MagicMock()
    client.chat.create.return_value = mock_chat

    return client


def test_batch_initialization(mock_client):
    batch = Batch(name="test-batch", client=mock_client)

    # Asserts creation call
    mock_client.batch.create.assert_called_once_with(batch_name="test-batch")
    assert batch.batch_id == "batch_abc123"


def test_add_request_to_batch(mock_client):
    """Test that adding a request to the batch correctly creates a chat and appends messages."""
    batch = Batch(
        name="test-batch",
        system_prompt="You are a helpful bot.",
        client=mock_client,
    )

    batch.add_request_to_batch(message="Hello world", batch_request_id="req_001")

    # Asserts chat creation call
    mock_client.chat.create.assert_called_once()
    assert len(batch.batch_requests) == 1

    # Verify message appends (system + user)
    mock_chat = mock_client.chat.create.return_value
    assert mock_chat.append.call_count == 2
    assert "You are a helpful bot." in str(mock_chat.append.call_args_list[0])
    assert "Hello world" in str(mock_chat.append.call_args_list[1])


def test_run_batch(mock_client):
    batch = Batch(name="test-batch", client=mock_client)
    batch.add_request_to_batch("Hello", "req_001")

    batch.run_batch()

    # Asserts batch.add was invoked with correct arguments
    mock_client.batch.add.assert_called_once_with(
        batch_id="batch_abc123", batch_requests=batch.batch_requests
    )


def test_add_images_to_batch():
    """Verify exactly batch_size items are added (prevents off-by-one errors)."""
    fake_images = [f"http://img.com/{i}.jpg" for i in range(20)]

    batch = Batch(name="test-batch", client=MagicMock(), batch_size=5)

    batch.add_images_to_batch(fake_images)

    # Asserts batch_requests was updated.
    assert len(batch.batch_requests) == 5

    # Inspect mock chat objects appended to batch_requests
    first_chat_mock = batch.batch_requests[0]
    # Check that append was called with user message containing image URL
    user_call_arg = first_chat_mock.append.call_args_list[0]
    assert "http://img.com/0.jpg" in str(user_call_arg)
    user_call_arg = first_chat_mock.append.call_args_list[1]
    assert "http://img.com/1.jpg" in str(user_call_arg)
