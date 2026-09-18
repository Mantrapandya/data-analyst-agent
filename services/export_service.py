"""Data and Report Export Service."""

import json
import os
import io
import pandas as pd


def export_cleaned_csv(df):
    """Export DataFrame as CSV bytes/string."""
    return df.to_csv(index=False)


def export_analysis_json(dataset_dict, profile, insights, anomalies, correlations):
    """Export full structured analytical findings as JSON."""
    payload = {
        "dataset": dataset_dict,
        "profile": profile,
        "insights": insights,
        "anomalies": anomalies,
        "correlations": {
            "columns": correlations.get("columns", []),
            "matrix": correlations.get("matrix", {}),
            "top_positive": correlations.get("top_positive", []),
            "top_negative": correlations.get("top_negative", []),
            "disclaimer": correlations.get("disclaimer", "")
        }
    }
    return json.dumps(payload, indent=2, default=str)
