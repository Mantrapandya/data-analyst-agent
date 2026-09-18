"""Test safe cleaning pipeline."""

import pandas as pd
from services.cleaning_service import detect_issues, apply_cleaning


def test_detect_and_clean_pipeline():
    # DataFrame with missing, duplicates, and whitespace
    df = pd.DataFrame({
        "name": [" Alice ", "Bob", " Alice ", "Charlie", "David"],
        "age": [25.0, 30.0, 25.0, None, 40.0],
        "score": ["100", "85", "100", "92", "78"]  # numeric stored as string
    })

    issues = detect_issues(df)
    assert len(issues) >= 3

    cleaned_df, changelog = apply_cleaning(df)
    
    # Original must not have been modified
    assert len(df) == 5

    # Cleaned should have 4 rows (1 duplicate removed)
    assert len(cleaned_df) == 4
    # Whitespace stripped
    assert cleaned_df["name"].iloc[0] == "Alice"
    # Missing age filled with median
    assert cleaned_df["age"].isnull().sum() == 0
    # Score converted to numeric
    assert pd.api.types.is_numeric_dtype(cleaned_df["score"])
    assert len(changelog) > 0
