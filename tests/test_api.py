
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_list_flights_endpoint():
    response = client.get("/flights/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_flight_list_pagination_validation():
    response = client.get("/flights/?limit=0")

    assert response.status_code == 422
