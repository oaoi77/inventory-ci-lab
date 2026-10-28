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
