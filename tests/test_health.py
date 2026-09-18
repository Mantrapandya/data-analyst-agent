"""Test /api/health endpoint."""


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "Data Analyst Agent"
    assert "version" in data
