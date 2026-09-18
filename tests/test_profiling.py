"""Test dataset profiling and data health score methodology."""

import pandas as pd
from services.profiling_service import profile_dataset, calculate_health_score


def test_profiling_service(sample_dataframe):
    profile = profile_dataset(sample_dataframe)
    
    # Verify overview
    assert profile["overview"]["rows"] == 5
    assert profile["overview"]["columns"] == 11
    assert profile["overview"]["numeric_columns"] >= 5
    assert profile["overview"]["categorical_columns"] >= 2
    
    # Verify quality
    assert profile["quality"]["total_missing"] == 0
    assert profile["quality"]["duplicate_rows"] == 0
    assert profile["health_score"] >= 80

    # Verify column statistics
    rev_col = profile["columns"]["revenue"]
    assert rev_col["type"] == "numeric"
    assert rev_col["mean"] > 0
    assert rev_col["min"] == 150.0
    assert rev_col["max"] == 475.0


def test_health_score_penalties():
    # Construct messy dataset
    df_messy = pd.DataFrame({
        "a": [1, None, None, None, 5],
        "b": ["dup", "dup", "dup", "dup", "dup"],
        "c": [10, 10, 10, 10, 10]  # Constant column
    })
    profile = profile_dataset(df_messy)
    # Score should be significantly lower due to missing, constant, and duplicates
    assert profile["health_score"] < 70
