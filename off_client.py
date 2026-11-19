import requests

BASE_URL = "https://world.openfoodfacts.org"
HEADERS =  {"User-Agent": "InventoryManager/1.0 (student project)"}

def _simplify(p):
    """Return a simplified product dictionary with only the fields we care about."""
    return {
         "product_name": p.get("product_name", ""),
        "brands": p.get("brands", ""),
        "ingredients_text": p.get("ingredients_text", ""),
        "barcode": p.get("code", ""),
    }

def fetch_by_barcode(barcode):
    """Fetch a product by barcode from the Open Food Facts API."""
    url = f"{BASE_URL}/api/v0/product/{barcode}.json"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return None
    data = response.json()
    if data.get("status") != 1:
        return None
    return _simplify(data["product"])

def search_by_name(name):
    """Search for products by name from the Open Food Facts API."""
    url = f"{BASE_URL}/cgi/search.pl"
    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
    }
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code != 200:
        return []
    data = response.json()
    products = data.get("products", [])
    return [_simplify(p) for p in products]