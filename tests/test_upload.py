"""Test file upload validation, parsing, and rejection."""

import io


def test_upload_valid_csv(client):
    csv_content = b"col_a,col_b,col_c\n1,apple,10.5\n2,banana,20.0\n3,orange,15.2\n"
    data = {
        "file": (io.BytesIO(csv_content), "test_data.csv")
    }
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 201
    res_data = response.get_json()
    assert res_data["success"] is True
    assert res_data["dataset"]["row_count"] == 3
    assert res_data["dataset"]["col_count"] == 3
    assert "health_score" in res_data["dataset"]


def test_upload_empty_file(client):
    data = {
        "file": (io.BytesIO(b""), "empty.csv")
    }
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    assert "empty" in response.get_json()["error"].lower()


def test_upload_unsupported_extension(client):
    data = {
        "file": (io.BytesIO(b"dummy data"), "script.exe")
    }
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    assert "unsupported" in response.get_json()["error"].lower()


def test_upload_no_file(client):
    response = client.post("/api/upload", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
