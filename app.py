"""Simple FlasK Rest API for managing a list of items."""
from flask import Flask, jsonify, request

app = Flask(__name__)

inventory = [
    {"id": 1, "name": "Organic Almond Milk", "price": 4.99, "stock": 25,
     "barcode": "0025293002060",
     "details": {"status": 1, "product": {
         "product_name": "Organic Almond Milk", "brands": "Silk",
         "ingredients_text": "Filtered water, almonds, cane sugar, sea salt"}}},
    {"id": 2, "name": "Crunchy Peanut Butter", "price": 3.49, "stock": 40,
     "barcode": "0051500255162",
     "details": {"status": 1, "product": {
         "product_name": "Crunchy Peanut Butter", "brands": "Jif",
         "ingredients_text": "Roasted peanuts, sugar, molasses, salt"}}},
    {"id": 3, "name": "Whole Grain Oats", "price": 5.25, "stock": 18,
     "barcode": "0030000010204",
     "details": {"status": 1, "product": {
         "product_name": "Whole Grain Oats", "brands": "Quaker",
         "ingredients_text": "100% whole grain rolled oats"}}},
]

def find_item(item_id):
  return next((item for item in inventory if item["id"] == item_id), None)

def next_id():
  return max((i["id"] for i in inventory), default=0) + 1

def check(data, required=()):
    """Return an error message if the data is invalid, otherwise None."""
    if not isinstance(data, dict):
        return "JSON body required"
    for field in required:
        if field not in data:
            return f"Missing field: {field}"
    if "price" in data and (not isinstance(data["price"], (int, float)) or data["price"] < 0):
        return "price must be a non-negative number"
    if "stock" in data and (not isinstance(data["stock"], int) or data["stock"] < 0):
        return "stock must be a non-negative integer"
    return None

#CRUD

@app.get("/inventory")
def get_inventory():
  return jsonify(inventory)

@app.get("/inventory/<int:item_id>")
def get_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item)

@app.post("/inventory")
def add_item():
    data = request.get_json()
    error = check(data, required=("name", "price", "stock"))
    if error:
        return jsonify({"error": error}), 400
    item = {
        "id": next_id(),
        "name": data["name"],
        "price": data["price"],
        "stock": data["stock"],
        "barcode": data.get("barcode", ""),
        "details": data.get("details", {})
    }
    inventory.append(item)
    return jsonify(item), 201

@app.patch("/inventory/<int:item_id>")
def update_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    data = request.get_json()
    error = check(data)
    if error:
        return jsonify({"error": error}), 400
    for field in ("name", "price", "stock", "barcode", "details"):
        if field in data:
            item[field] = data[field]
    return jsonify(item)

@app.delete("/inventory/<int:item_id>")
def delete_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    inventory.remove(item)
    return jsonify({"message": "Item deleted"})
