import os
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.get('/')
def index():
    return jsonify(service='inventory-api', version=os.getenv('APP_VERSION', 'dev'), status='running')

@app.get('/health')
def health():
    return jsonify(status='ok'), 200

@app.get('/api/items')
def items():
    # Lab dataset: in a real system this would be backed by a database.
    return jsonify(items=[{'id': 1, 'name': 'router', 'stock': 8},
                          {'id': 2, 'name': 'switch', 'stock': 3}])

@app.get('/api/items/low-stock')
def low_stock():
    raw = request.args.get('threshold')
    if raw is None:
        return jsonify(error='threshold is required'), 400
    try:
        threshold = int(raw)
    except ValueError:
        return jsonify(error='threshold must be an integer'), 400
    if threshold < 0 or threshold > 100:
        return jsonify(error='threshold must be between 0 and 100'), 400

    all_items = [{'id': 1, 'name': 'router', 'stock': 8},
                 {'id': 2, 'name': 'switch', 'stock': 3}]
    result = [i for i in all_items if i['stock'] < threshold]
    return jsonify(items=result), 200


@app.get('/api/items/<int:item_id>')
def item_detail(item_id):
    data = {1: {'id': 1, 'name': 'router', 'stock': 8},
            2: {'id': 2, 'name': 'switch', 'stock': 3}}
    if item_id not in data:
        return jsonify(error='item not found'), 404
    return jsonify(data[item_id]), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
