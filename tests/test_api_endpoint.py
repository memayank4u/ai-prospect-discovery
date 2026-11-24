from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_invalid_query():
    response = client.post("/prospect-discovery", json={"query": "  "})
    assert response.status_code == 422


def test_prospect_discovery_endpoint():
    response = client.post("/prospect-discovery", json={"query": "Football lovers in Washington DC in USA"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["query"] == "Football lovers in Washington DC in USA"
    assert "total_prospects" in data
    assert isinstance(data["prospects"], list)
