from unittest.mock import patch, MagicMock
import requests
import cli

ITEM = {"id": 1, "name": "Milk", "price": 2.5, "stock": 5, "details": None}


def fake_response(data, status=200):
    m = MagicMock()
    m.ok = status < 400
    m.status_code = status
    m.json.return_value = data
    return m


@patch("cli.requests.request")
def test_list(mock_req, capsys):
    mock_req.return_value = fake_response([ITEM])
    assert cli.main(["list"]) == 0
    assert "Milk" in capsys.readouterr().out


@patch("cli.requests.request")
def test_view(mock_req, capsys):
    mock_req.return_value = fake_response(ITEM)
    assert cli.main(["view", "1"]) == 0
    assert "Milk" in capsys.readouterr().out


@patch("cli.requests.request")
def test_view_404(mock_req, capsys):
    mock_req.return_value = fake_response({"error": "Item not found"}, 404)
    assert cli.main(["view", "99"]) == 1
    assert "Item not found" in capsys.readouterr().out


@patch("cli.requests.request")
def test_add_payload(mock_req):
    mock_req.return_value = fake_response(ITEM, 201)
    cli.main(["add", "Milk", "--price", "2.5", "--stock", "5"])
    assert mock_req.call_args.kwargs["json"] == {"name": "Milk", "price": 2.5, "stock": 5}


@patch("cli.requests.request")
def test_update(mock_req, capsys):
    mock_req.return_value = fake_response(ITEM)
    assert cli.main(["update", "1", "--price", "3"]) == 0
    assert mock_req.call_args.kwargs["json"] == {"price": 3.0}


@patch("cli.requests.request")
def test_update_needs_a_field(mock_req):
    assert cli.main(["update", "1"]) == 1
    mock_req.assert_not_called()


@patch("cli.requests.request")
def test_delete(mock_req, capsys):
    mock_req.return_value = fake_response({"message": "Item 1 deleted"})
    assert cli.main(["delete", "1"]) == 0
    assert "deleted" in capsys.readouterr().out


@patch("cli.requests.request")
def test_lookup(mock_req, capsys):
    mock_req.return_value = fake_response(
        {"products": [{"product_name": "Oat Milk", "brands": "Oatly", "barcode": "9"}]})
    assert cli.main(["lookup", "--name", "oat"]) == 0
    assert "Oat Milk" in capsys.readouterr().out


@patch("cli.requests.request")
def test_import(mock_req, capsys):
    mock_req.return_value = fake_response(ITEM, 201)
    assert cli.main(["import", "123", "--price", "4.5", "--stock", "3"]) == 0
    assert mock_req.call_args.kwargs["json"] == {"barcode": "123", "price": 4.5, "stock": 3}
    assert "Imported" in capsys.readouterr().out


@patch("cli.requests.request", side_effect=requests.ConnectionError())
def test_server_down(mock_req, capsys):
    assert cli.main(["list"]) == 1
    assert "could not reach" in capsys.readouterr().out