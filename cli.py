"""Command-line interface for the inventory API."""
import argparse
import sys
import requests

API_URL = "http://127.0.0.1:5000"


def call_api(method, path, **kwargs):
    """Call the API. Print an error and return None if anything goes wrong."""
    try:
        resp = requests.request(method, API_URL + path, timeout=15, **kwargs)
    except requests.RequestException:
        print("Error: could not reach the API. Is the server running?")
        return None
    body = resp.json()
    if not resp.ok:
        print(f"Error {resp.status_code}: {body.get('error')}")
        return None
    return body


def show(item):
    print(f"[{item['id']}] {item['name']} | ${item['price']:.2f} | stock: {item['stock']}")


def cmd_list(args):
    items = call_api("GET", "/inventory")
    if items is None:
        return 1
    for item in items:
        show(item)
    return 0


def cmd_view(args):
    item = call_api("GET", f"/inventory/{args.id}")
    if item is None:
        return 1
    show(item)
    product = (item.get("details") or {}).get("product")
    if product:
        print(f"Brand: {product['brands']}\nIngredients: {product['ingredients_text']}")
    return 0


def cmd_add(args):
    payload = {"name": args.name, "price": args.price, "stock": args.stock}
    if args.barcode:
        payload["barcode"] = args.barcode
    item = call_api("POST", "/inventory", json=payload)
    if item is None:
        return 1
    print("Added:")
    show(item)
    return 0


def cmd_update(args):
    payload = {}
    if args.price is not None:
        payload["price"] = args.price
    if args.stock is not None:
        payload["stock"] = args.stock
    if not payload:
        print("Error: provide --price and/or --stock")
        return 1
    item = call_api("PATCH", f"/inventory/{args.id}", json=payload)
    if item is None:
        return 1
    print("Updated:")
    show(item)
    return 0


def cmd_delete(args):
    result = call_api("DELETE", f"/inventory/{args.id}")
    if result is None:
        return 1
    print(result["message"])
    return 0


def cmd_lookup(args):
    params = {"barcode": args.barcode} if args.barcode else {"name": args.name}
    result = call_api("GET", "/lookup", params=params)
    if result is None:
        return 1
    for p in result.get("products") or [result["product"]]:
        print(f"{p['product_name']} | {p['brands']} | {p['barcode']}")
    return 0


def cmd_import(args):
    payload = {"barcode": args.barcode, "price": args.price, "stock": args.stock}
    item = call_api("POST", "/inventory/import", json=payload)
    if item is None:
        return 1
    print("Imported from OpenFoodFacts:")
    show(item)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Inventory manager CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all items").set_defaults(func=cmd_list)

    p = sub.add_parser("view", help="View one item")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_view)

    p = sub.add_parser("add", help="Add an item")
    p.add_argument("name")
    p.add_argument("--price", type=float, required=True)
    p.add_argument("--stock", type=int, required=True)
    p.add_argument("--barcode")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("update", help="Update price or stock")
    p.add_argument("id", type=int)
    p.add_argument("--price", type=float)
    p.add_argument("--stock", type=int)
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("delete", help="Delete an item")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("lookup", help="Find a product on OpenFoodFacts")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--barcode")
    group.add_argument("--name")
    p.set_defaults(func=cmd_lookup)

    p = sub.add_parser("import", help="Import a product from OpenFoodFacts")
    p.add_argument("barcode")
    p.add_argument("--price", type=float, required=True)
    p.add_argument("--stock", type=int, required=True)
    p.set_defaults(func=cmd_import)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())