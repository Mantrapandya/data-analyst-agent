"""Data profiling and health score computation."""

import pandas as pd
import numpy as np


def profile_dataset(df):
    """Generate a comprehensive data profile for the given DataFrame.

    Returns a dictionary with overview, quality, column details, and health score.
    """
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

    total_cells = len(df) * len(df.columns)
    total_missing = int(df.isnull().sum().sum())
    duplicate_count = int(df.duplicated().sum())

    profile = {
        "overview": {
            "rows": len(df),
            "columns": len(df.columns),
            "memory_usage_bytes": int(df.memory_usage(deep=True).sum()),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
            "numeric_columns": len(numeric_cols),
            "categorical_columns": len(categorical_cols),
            "datetime_columns": len(datetime_cols),
        },
        "quality": {
            "total_cells": total_cells,
            "total_missing": total_missing,
            "missing_percentage": round(total_missing / total_cells * 100, 2) if total_cells > 0 else 0,
            "duplicate_rows": duplicate_count,
            "duplicate_percentage": round(duplicate_count / len(df) * 100, 2) if len(df) > 0 else 0,
            "complete_rows": int((~df.isnull().any(axis=1)).sum()),
            "complete_percentage": round((~df.isnull().any(axis=1)).sum() / len(df) * 100, 2) if len(df) > 0 else 0,
        },
        "columns": {},
    }

    # Constant columns (only one unique non-null value)
    constant_cols = []
    for col in df.columns:
        if df[col].dropna().nunique() <= 1:
            constant_cols.append(col)
    profile["quality"]["constant_columns"] = constant_cols
    profile["quality"]["constant_column_count"] = len(constant_cols)

    # Per-column profiling
    for col in df.columns:
        col_data = df[col]
        missing = int(col_data.isnull().sum())
        missing_pct = round(missing / len(df) * 100, 2) if len(df) > 0 else 0
        unique = int(col_data.nunique())

        col_profile = {
            "name": col,
            "dtype": str(col_data.dtype),
            "missing": missing,
            "missing_percentage": missing_pct,
            "unique": unique,
            "unique_percentage": round(unique / len(df) * 100, 2) if len(df) > 0 else 0,
        }

        if col in numeric_cols:
            col_profile["type"] = "numeric"
            desc = col_data.describe()
            col_profile.update({
                "mean": _safe_float(col_data.mean()),
                "median": _safe_float(col_data.median()),
                "std": _safe_float(col_data.std()),
                "min": _safe_float(col_data.min()),
                "max": _safe_float(col_data.max()),
                "q25": _safe_float(desc.get("25%", None)),
                "q75": _safe_float(desc.get("75%", None)),
                "skewness": _safe_float(col_data.skew()),
                "zeros": int((col_data == 0).sum()),
                "negatives": int((col_data < 0).sum()),
            })
        elif col in datetime_cols:
            col_profile["type"] = "datetime"
            valid = col_data.dropna()
            if len(valid) > 0:
                col_profile.update({
                    "min": str(valid.min()),
                    "max": str(valid.max()),
                    "range_days": (valid.max() - valid.min()).days,
                })
        else:
            col_profile["type"] = "categorical"
            value_counts = col_data.value_counts().head(10)
            col_profile.update({
                "top_values": {str(k): int(v) for k, v in value_counts.items()},
                "top_value": str(value_counts.index[0]) if len(value_counts) > 0 else None,
                "top_frequency": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
            })

        profile["columns"][col] = col_profile

    # Calculate health score
    profile["health_score"] = calculate_health_score(df, profile)

    return profile


def calculate_health_score(df, profile):
    """Calculate a transparent data health score (0-100).

    Methodology:
    - Completeness (30 pts): Penalty for missing values
    - Uniqueness (20 pts): Penalty for duplicate rows
    - Consistency (20 pts): Penalty for constant columns and type issues
    - Validity (15 pts): Penalty for outlier ratio
    - Richness (15 pts): Reward for having diverse column types
    """
    if len(df) == 0:
        return 0

    total_cells = profile["quality"]["total_cells"]
    total_missing = profile["quality"]["total_missing"]

    # 1. Completeness (30 points)
    missing_ratio = total_missing / total_cells if total_cells > 0 else 0
    completeness = 30 * (1 - missing_ratio)

    # 2. Uniqueness (20 points)
    dup_ratio = profile["quality"]["duplicate_rows"] / len(df) if len(df) > 0 else 0
    uniqueness = 20 * (1 - dup_ratio)

    # 3. Consistency (20 points)
    num_cols = len(df.columns)
    constant_ratio = len(profile["quality"]["constant_columns"]) / num_cols if num_cols > 0 else 0
    consistency = 20 * (1 - constant_ratio)

    # 4. Validity (15 points) - based on outlier ratio in numeric columns
    numeric_cols = df.select_dtypes(include="number").columns
    if len(numeric_cols) > 0:
        outlier_counts = 0
        total_numeric_values = 0
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) > 10:
                q1 = data.quantile(0.25)
                q3 = data.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    outlier_counts += int(((data < lower) | (data > upper)).sum())
                total_numeric_values += len(data)
        outlier_ratio = outlier_counts / total_numeric_values if total_numeric_values > 0 else 0
        validity = 15 * max(0, 1 - outlier_ratio * 5)  # Penalize heavily for outliers
    else:
        validity = 15

    # 5. Richness (15 points) - reward diverse column types
    type_count = sum([
        1 if profile["overview"]["numeric_columns"] > 0 else 0,
        1 if profile["overview"]["categorical_columns"] > 0 else 0,
        1 if profile["overview"]["datetime_columns"] > 0 else 0,
    ])
    richness = 15 * (type_count / 3)

    score = round(completeness + uniqueness + consistency + validity + richness)
    return max(0, min(100, score))


def _safe_float(value):
    """Convert value to float, handling NaN/inf."""
    if value is None:
        return None
    try:
        f = float(value)
        if np.isnan(f) or np.isinf(f):
            return None
        return round(f, 4)
    except (TypeError, ValueError):
        return None
