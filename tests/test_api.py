from fastapi.testclient import TestClient
import pytest
from src.api import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    response = client.get("/health")
    assert response.status_code in [200, 503]


def test_get_stats():
    response = client.get("/stats")
    if response.status_code == 200:
        data = response.json()
        assert "total_records" in data
        assert "avg_closed_price" in data


def test_get_latest_price():
    response = client.get("/prices/latest")
    if response.status_code == 200:
        data = response.json()
        assert "date" in data
        assert "closed_price" in data


def test_get_prices_pagination():
    response = client.get("/prices?limit=10&skip=0")
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10