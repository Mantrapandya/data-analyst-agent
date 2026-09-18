"""End-to-end smoke test covering the entire analytics workflow."""

import json


def test_end_to_end_workflow(client):
    # 1. Verify health
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"

    # 2. Load sample dataset
    res = client.post("/api/sample")
    assert res.status_code == 201
    dataset = res.get_json()["dataset"]
    dataset_id = dataset["id"]
    assert dataset_id > 0

    # 3. Verify profiling
    res = client.get(f"/api/datasets/{dataset_id}")
    assert res.status_code == 200
    profile = res.get_json()["profile"]
    assert profile["overview"]["rows"] >= 500

    # 4. Preview table
    res = client.get(f"/api/datasets/{dataset_id}/preview?limit=10")
    assert res.status_code == 200
    assert len(res.get_json()["data"]) == 10

    # 5. Clean dataset
    res = client.post(f"/api/datasets/{dataset_id}/clean", json={"mode": "apply"})
    assert res.status_code == 200
    assert res.get_json()["success"] is True

    # 6. Verify EDA charts
    res = client.get(f"/api/datasets/{dataset_id}/eda")
    assert res.status_code == 200
    assert res.get_json()["total_charts"] > 0

    # 7. Check anomalies
    res = client.get(f"/api/datasets/{dataset_id}/anomalies")
    assert res.status_code == 200
    assert "total_anomalies" in res.get_json()

    # 8. Check correlations
    res = client.get(f"/api/datasets/{dataset_id}/correlations")
    assert res.status_code == 200
    assert "matrix" in res.get_json()

    # 9. Ask Your Data
    res = client.post(f"/api/datasets/{dataset_id}/ask", json={"question": "What is the total revenue?"})
    assert res.status_code == 200
    assert "answer" in res.get_json()
    assert "sql_used" in res.get_json()

    # 10. Generate report
    res = client.get(f"/api/datasets/{dataset_id}/report?format=json")
    assert res.status_code == 200
    assert "markdown" in res.get_json()
    assert "html" in res.get_json()
