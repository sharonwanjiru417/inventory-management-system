from unittest.mock import patch, MagicMock 
import pytest
import requests
import off_client

def mock_response(data):
    m = MagicMock()
    m.json.return_value = data
    return m


@patch("off_client.requests.get")
def test_fetch_by_barcode(mock_get):
    mock_get.return_value = mock_response(
        {"status": 1, "product": {"product_name": "Milk", "brands": "Silk", "code": "1"}})
    assert off_client.fetch_by_barcode("1")["brands"] == "Silk"


@patch("off_client.requests.get")
def test_fetch_not_found(mock_get):
    mock_get.return_value = mock_response({"status": 0})
    assert off_client.fetch_by_barcode("000") is None


@patch("off_client.requests.get")
def test_search_by_name(mock_get):
    mock_get.return_value = mock_response({"products": [{"product_name": "Oat Milk"}]})
    assert off_client.search_by_name("oat")[0]["product_name"] == "Oat Milk"


@patch("off_client.requests.get", side_effect=requests.ConnectionError())
def test_network_failure_raises(mock_get):
    with pytest.raises(requests.RequestException):
        off_client.fetch_by_barcode("1")