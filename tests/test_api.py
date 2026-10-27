
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


def test_country_analytics_endpoint():
    response = client.get("/analytics/countries")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_summary_analytics_endpoint():
    response = client.get("/analytics/summary")

    assert response.status_code == 200

    body = response.json()
    assert body["total_flights"] >= 0
    assert "average_velocity" in body
    assert body["on_ground_count"] >= 0
