"""Test correlation analysis service."""

import pandas as pd
from services.correlation_service import calculate_correlations


def test_correlation_analysis():
    df = pd.DataFrame({
        "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        "y": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],  # perfect positive
        "z": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]         # perfect negative
    })
    res = calculate_correlations(df)
    assert len(res["top_positive"]) > 0
    assert res["top_positive"][0]["correlation"] > 0.99
    assert len(res["top_negative"]) > 0
    assert res["top_negative"][0]["correlation"] < -0.99
    assert "disclaimer" in res
