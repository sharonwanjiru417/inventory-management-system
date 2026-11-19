# inventory-management-system
Flask Inventory Management system API with Open food Facts integration and CLI
[OpenFoodFacts API](https://world.openfoodfacts.org/data) by barcode or name and imported straight into the inventory.

Inventory is stored in an in-memory Python list that simulates a database.

## Table of Contents

1. [Features](#features)
2. [Project Structure](#project-structure)
3. [Architecture](#architecture)
4. [Installation and Setup](#installation-and-setup)
5. [Running the Application](#running-the-application)
6. [Data Model](#data-model)
7. [API Endpoints](#api-endpoints)
8. [CLI Usage](#cli-usage)
9. [Running the Tests](#running-the-tests)
10. [Debugging and Manual Testing](#debugging-and-manual-testing)
11. [Git Workflow](#git-workflow)
12. [Design Notes and Limitations](#design-notes-and-limitations)
13. [Troubleshooting](#troubleshooting)

---
## Features

- **Full CRUD** on inventory items (`GET`, `POST`, `PATCH`, `DELETE`)
- **Input validation** with clear JSON error messages and correct HTTP status codes
- **OpenFoodFacts lookup**: search products by barcode or name
- **Import from API**: fetch a product from OpenFoodFacts and add it to the inventory array in one step
- **CLI** for every operation, with friendly error handling for bad input, server downtime and API failures
- **Test suite** (pytest + `unittest.mock`) covering the API, the external client and the CLI, with no real network calls

## Project Structure

```
inventory-management-system/
├── app.py                 # Flask API: routes, validation, mock database
├── off_client.py          # OpenFoodFacts client (barcode lookup, name search)
├── cli.py                 # Command-line interface that calls the API
├── requirements.txt
├── README.md
├── .gitignore
└── tests/
    ├── test_api.py        # Endpoint tests
    ├── test_off_client.py # External API client tests (mocked)
    └── test_cli.py        # CLI command tests (mocked)
```

## Architecture

```
┌──────────┐   HTTP    ┌───────────────┐   HTTPS   ┌──────────────────┐
│  cli.py  │ ────────▶ │    app.py     │ ────────▶ │  OpenFoodFacts   │
│  (user)  │ ◀──────── │ (Flask + list)│ ◀──────── │  (via off_client)│
└──────────┘   JSON    └───────────────┘   JSON    └──────────────────┘
```

| Module | Responsibility |
|---|---|
| `app.py` | Routing, request validation, and reading/writing the inventory array |
| `off_client.py` | All communication with OpenFoodFacts |
| `cli.py` | Parsing user commands, calling the API, and printing results or errors |

## Installation and Setup

**Requirements:** Python 3.9+ and Git.

```bash
# 1. Clone the repository
git clone <https://github.com/sharonwanjiru417/inventory-management-system.git>
cd inventory-manager

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        

# 3. Install dependencies
pip install -r requirements.txt
```

`requirements.txt` should contain at least:

```
flask
requests
pytest
```

## Running the Application

The CLI talks to the API over HTTP, so use **two terminals** (both with the virtual environment activated).

**Terminal 1: start the API**

```bash
python app.py
```

The server runs at `http://127.0.0.1:5000` in debug mode (auto-reload and in-browser tracebacks).

**Terminal 2: use the CLI**

```bash
python cli.py list
```

## Data Model

Each inventory item has this shape. The `details` field mirrors the OpenFoodFacts response format.

```json
{
  "id": 1,
  "name": "Organic Almond Milk",
  "price": 4.99,
  "stock": 25,
  "barcode": "0025293002060",
  "details": {
    "status": 1,
    "product": {
      "product_name": "Organic Almond Milk",
      "brands": "Silk",
      "ingredients_text": "Filtered water, almonds, cane sugar, sea salt"
    }
  }
}
```

| Field | Type | Rules |
|---|---|---|
| `id` | integer | Assigned by the server, never reused within a session |
| `name` | string | Required when adding |
| `price` | number | Required when adding, `>= 0` |
| `stock` | integer | Required when adding, `>= 0` |
| `barcode` | string or null | Optional |
| `details` | object or null | Filled from OpenFoodFacts when an item is imported |

The app starts with three sample items so you can try every command immediately.

## API Endpoints

| Method | Endpoint | Description | Success | Errors |
|---|---|---|---|---|
| GET | `/inventory` | List all items | 200 | none |
| GET | `/inventory/<id>` | Get one item | 200 | 404 |
| POST | `/inventory` | Add an item | 201 | 400 |
| PATCH | `/inventory/<id>` | Update `name`, `price` and/or `stock` | 200 | 400, 404 |
| DELETE | `/inventory/<id>` | Remove an item | 200 | 404 |
| GET | `/lookup` | Search OpenFoodFacts by `?barcode=` or `?name=` | 200 | 400, 404, 502 |
| POST | `/inventory/import` | Fetch a product from OpenFoodFacts and add it | 201 | 400, 404, 502 |

All errors return JSON in the form `{"error": "message"}`.

### GET /inventory

```bash
curl http://127.0.0.1:5000/inventory
```

Returns a JSON array of all items.

### GET /inventory/\<id\>

```bash
curl http://127.0.0.1:5000/inventory/1
```

Returns one item. An unknown id returns `404 {"error": "Item not found"}`.

### POST /inventory

```bash
curl -X POST http://127.0.0.1:5000/inventory \
  -H "Content-Type: application/json" \
  -d '{"name": "Green Tea", "price": 3.5, "stock": 20, "barcode": "5000127281752"}'
```

Response `201`:

```json
{ "id": 4, "name": "Green Tea", "price": 3.5, "stock": 20, "barcode": "5000127281752", "details": null }
```

`name`, `price` and `stock` are required. Missing or invalid fields return `400`, for example `{"error": "Missing field: price"}`. To fill in OpenFoodFacts details automatically, use `/inventory/import` instead.

### PATCH /inventory/\<id\>

```bash
curl -X PATCH http://127.0.0.1:5000/inventory/1 \
  -H "Content-Type: application/json" \
  -d '{"price": 5.25, "stock": 30}'
```

Returns the updated item. Only `name`, `price` and `stock` can be changed; other fields in the body are ignored.

### DELETE /inventory/\<id\>

```bash
curl -X DELETE http://127.0.0.1:5000/inventory/2
```

```json
{ "message": "Item 2 deleted" }
```

### GET /lookup

Search OpenFoodFacts without changing the inventory.

```bash
curl "http://127.0.0.1:5000/lookup?barcode=3017620422003"
curl "http://127.0.0.1:5000/lookup?name=nutella"
```

Barcode response:

```json
{ "status": 1, "product": { "product_name": "Nutella", "brands": "Ferrero", "ingredients_text": "...", "barcode": "3017620422003" } }
```

Name response (up to 5 matches):

```json
{ "products": [ { "product_name": "...", "brands": "...", "barcode": "..." } ] }
```

| Status | Meaning |
|---|---|
| 400 | Neither `barcode` nor `name` was given |
| 404 | Barcode not found on OpenFoodFacts |
| 502 | OpenFoodFacts is unreachable or returned an error |

### POST /inventory/import

Fetches a product from OpenFoodFacts by barcode and **adds it to the inventory array**. The product name and details come from OpenFoodFacts, while you supply the price and stock.

```bash
curl -X POST http://127.0.0.1:5000/inventory/import \
  -H "Content-Type: application/json" \
  -d '{"barcode": "3017620422003", "price": 4.99, "stock": 12}'
```

| Status | Meaning |
|---|---|
| 201 | Imported and added |
| 400 | Missing `barcode`, `price` or `stock`, or invalid values |
| 404 | Barcode not found on OpenFoodFacts |
| 502 | OpenFoodFacts is unreachable or returned an error |

## CLI Usage

Make sure the API is running first. Run `python cli.py --help` or `python cli.py <command> --help` for built-in help.

| Command | Description |
|---|---|
| `list` | Show all items |
| `view <id>` | Show one item with its OpenFoodFacts details |
| `add <name> --price P --stock S [--barcode B]` | Add an item |
| `update <id> [--price P] [--stock S]` | Update price and/or stock |
| `delete <id>` | Delete an item |
| `lookup --barcode B` or `lookup --name N` | Find a product on OpenFoodFacts |
| `import <barcode> --price P --stock S` | Import a product from OpenFoodFacts into inventory |

### Examples

```bash
# View inventory
python cli.py list
python cli.py view 1

# Add an item manually
python cli.py add "Green Tea" --price 3.5 --stock 20

# Update price and stock
python cli.py update 1 --price 5.25 --stock 30
python cli.py update 3 --stock 50

# Delete an item
python cli.py delete 2
```

### Find a product on the API and add it to inventory

This is the main external-API workflow:

```bash
# 1. Search by name and note the barcode
python cli.py lookup --name "nutella"

# 2. Import it by barcode, setting your own price and stock
python cli.py import 3017620422003 --price 4.99 --stock 12

# 3. Confirm it is now in the inventory array
python cli.py list
```

### Error handling

| Situation | CLI behavior |
|---|---|
| Invalid input (`view abc`, missing `--price`) | argparse prints a usage message |
| `update 1` with no fields | `Error: provide --price and/or --stock` |
| Unknown id or product | `Error 404: Item not found` |
| API server not running | `Error: could not reach the API. Is the server running?` |
| OpenFoodFacts down | `Error 502: OpenFoodFacts is unavailable` |

Every command returns exit code `0` on success and `1` on failure, so it can be used in scripts.

## Running the Tests

```bash
python -m pytest -v
```

The tests use `unittest.mock` and pytest's `monkeypatch` to simulate OpenFoodFacts and the HTTP layer, so **no network access or running server is needed**.

| Feature | Test file | Covers |
|---|---|---|
| GET all / one | `test_api.py` | Success and 404 |
| POST | `test_api.py` | Valid and invalid input |
| PATCH | `test_api.py` | Success, 404, invalid values |
| DELETE | `test_api.py` | Success, repeat delete returns 404 |
| `/lookup` | `test_api.py` | Barcode, name, missing params, API down (502) |
| `/inventory/import` | `test_api.py` | Success (item added to array), 400, 404, 502 |
| OpenFoodFacts client | `test_off_client.py` | Barcode success, not found, name search, network error |
| CLI commands | `test_cli.py` | list, view, add, update, delete, lookup, import, server down, API errors |

A fixture in `test_api.py` restores the inventory list after each test, so tests do not affect each other.

## Debugging and Manual Testing

- **Flask debug mode:** `app.run(debug=True)` reloads on code changes and shows an interactive traceback on errors.
- **Postman:** create one request per endpoint (see [API Endpoints](#api-endpoints)). For POST and PATCH, set Body to *raw* and *JSON*. Also test the error paths: a missing field (400), an unknown id (404) and a negative price (400).

## Git Workflow

Each feature was developed on its own branch, merged through a pull request, and the branch deleted afterwards.

| Branch | Purpose |
|---|---|
| `feature/crud-routes` | CRUD routes, validation and mock data |
| `feature/openfoodfacts-client` | `off_client.py` and the `/lookup` route |
| `feature/import-route` | `/inventory/import` |
| `feature/cli` | CLI tool |
| `readme` | This README |

Only `main` remains after the final merge.

## Design Notes and Limitations

- **In-memory storage.** The inventory is a Python list, so data resets when the server restarts and is not safe for multiple server processes. A production version would use a database such as SQLite or PostgreSQL.
- **External API failures are handled.** Timeouts, connection errors and bad responses from OpenFoodFacts are caught in the routes and returned as `502`, so the app never crashes because of the external service.
- **IDs are never reused during a session.** The next id is the current maximum plus one.
- **Whitelisted updates.** `PATCH` only changes `name`, `price` and `stock`, so clients cannot overwrite `id` or `details`.
- **No duplicate check on import.** Importing the same barcode twice creates two items.
- **No authentication.** This is a lab project, so the admin portal is open. A real deployment would add login and role checks.
- **OpenFoodFacts data quality.** The data is crowdsourced, so some products have missing names or ingredients. The client returns empty strings for missing fields, and import falls back to `"Unnamed product"`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Error: could not reach the API` | Start the server with `python app.py` in another terminal |
| `ModuleNotFoundError: No module named 'flask'` | Activate the virtual environment and run `pip install -r requirements.txt` |
| `Address already in use` on port 5000 | Stop the other process, or on macOS disable AirPlay Receiver in System Settings |
| `ModuleNotFoundError: app` when running pytest | Run `python -m pytest` from the project root |
| Lookup or import returns `502` | OpenFoodFacts may be slow or down; retry in a moment |

## Author

Sharon Wanjiru
Moringa School