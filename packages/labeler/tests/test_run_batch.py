from unittest.mock import MagicMock


def parse_batch_response(result_item):
    """Your production logic for reading a single result from a batch."""
    # Example logic: extract text content
    return result_item.response.content


def test_parser_with_mock():
    # 1. Create a dummy object mimicking xAI batch result structure
    mock_item = MagicMock()
    mock_item.response.content = "【1巻】 吾輩は猫である"

    # 2. Test your parsing logic safely
    output = parse_batch_response(mock_item)
    assert output == "【1巻】 吾輩は猫である"
    print("Parser successfully handled mock object!")
