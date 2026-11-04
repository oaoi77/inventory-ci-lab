import pytest

from app.main import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'ok'

def test_items(client):
    response = client.get('/api/items')
    assert response.status_code == 200
    assert len(response.get_json()['items']) == 2

def test_item_not_found(client):
    response = client.get('/api/items/999')
    assert response.status_code == 404
    assert response.get_json()['error'] == 'item not found'

# challenge 1
def test_low_stock_filters_items(client):
    r = client.get('/api/items/low-stock?threshold=5')
    assert r.status_code == 200
    assert [i['name'] for i in r.get_json()['items']] == ['switch']
def test_low_stock_strictly_below(client):
    # switch co stock = 3, nen threshold=3 khong duoc tra ve switch
    r = client.get('/api/items/low-stock?threshold=3')
    assert r.get_json()['items'] == []
def test_low_stock_boundary_zero(client):
    r = client.get('/api/items/low-stock?threshold=0')
    assert r.status_code == 200
    assert r.get_json()['items'] == []
def test_low_stock_boundary_hundred(client):
    r = client.get('/api/items/low-stock?threshold=100')
    assert r.status_code == 200
    assert len(r.get_json()['items']) == 2
def test_low_stock_out_of_range(client):
    for bad in ['-1', '101']:
        r = client.get(f'/api/items/low-stock?threshold={bad}')
        assert r.status_code == 400
        assert 'error' in r.get_json()
def test_low_stock_not_integer(client):
    for bad in ['abc', '5.5']:
        r = client.get(f'/api/items/low-stock?threshold={bad}')
        assert r.status_code == 400
def test_low_stock_missing_threshold(client):
    r = client.get('/api/items/low-stock')
    assert r.status_code == 400