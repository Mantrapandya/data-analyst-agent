"""Test anomaly detection service."""

import pandas as pd
from services.anomaly_service import detect_anomalies


def test_anomaly_detection():
    # Construct data with an extreme outlier
    data = {
        "val": [10.0, 11.0, 10.5, 9.8, 10.2, 10.1, 10.4, 9.9, 10.3, 10.0, 1000.0]
    }
    df = pd.DataFrame(data)

    res = detect_anomalies(df, method="iqr")
    assert res["total_anomalies"] >= 1
    assert len(res["anomalous_records"]) >= 1
    assert res["anomalous_records"][0]["affected_columns"] == ["val"]
