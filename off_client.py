import requests

BASE_URL = "https://world.openfoodfacts.org"
HEADERS =  {"User-Agent": "InventoryManager/1.0 (student project)"}

def _simplify(p):
    """Keep only the fields we need."""
    return {
        "product_name": p.get("product_name", ""),
        "brands": p.get("brands", ""),
        "ingredients_text": p.get("ingredients_text", ""),
        "barcode": p.get("code", ""),
    }


def fetch_by_barcode(barcode):
    """Return a product dict, or None if the barcode is unknown."""
    r = requests.get(f"{BASE_URL}/api/v0/product/{barcode}.json",
                     headers=HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != 1:
        return None
    return _simplify(data["product"])


def search_by_name(name, limit=5):
    """Return a list of products matching a name."""
    r = requests.get(f"{BASE_URL}/cgi/search.pl", headers=HEADERS, timeout=10,
                     params={"search_terms": name, "search_simple": 1,
                             "action": "process", "json": 1, "page_size": limit})
    r.raise_for_status()
    return [_simplify(p) for p in r.json().get("products", [])]