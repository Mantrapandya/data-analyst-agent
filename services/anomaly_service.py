"""Anomaly detection using statistical methods."""

import pandas as pd
import numpy as np


def detect_anomalies(df, method="iqr", threshold=1.5):
    """Detect anomalies in numeric columns.

    Methods:
    - iqr: Interquartile Range method (default, robust)
    - zscore: Z-score method (assumes normal distribution)
    - isolation_forest: Isolation Forest (multivariate, requires sklearn)

    Returns dict with summary and list of anomalous records.
    """
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    if not numeric_cols:
        return {
            "method": method,
            "total_anomalies": 0,
            "columns_analyzed": 0,
            "column_details": [],
            "anomalous_records": [],
            "message": "No numeric columns available for anomaly detection.",
        }

    if method == "iqr":
        return _detect_iqr(df, numeric_cols, threshold)
    elif method == "zscore":
        return _detect_zscore(df, numeric_cols, threshold=3.0)
    elif method == "isolation_forest":
        return _detect_isolation_forest(df, numeric_cols)
    else:
        return _detect_iqr(df, numeric_cols, threshold)


def _detect_iqr(df, numeric_cols, threshold=1.5):
    """IQR-based anomaly detection per column."""
    anomaly_mask = pd.DataFrame(False, index=df.index, columns=numeric_cols)
    column_details = []

    for col in numeric_cols:
        data = df[col].dropna()
        if len(data) < 10:
            continue

        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1

        if iqr == 0:
            continue

        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr

        mask = (df[col] < lower) | (df[col] > upper)
        anomaly_mask[col] = mask
        count = int(mask.sum())

        if count > 0:
            column_details.append({
                "column": col,
                "method": "IQR",
                "count": count,
                "percentage": round(count / len(df) * 100, 2),
                "lower_bound": round(float(lower), 2),
                "upper_bound": round(float(upper), 2),
                "q1": round(float(q1), 2),
                "q3": round(float(q3), 2),
                "iqr": round(float(iqr), 2),
            })

    # Rows that are anomalous in any column
    any_anomaly = anomaly_mask.any(axis=1)
    anomalous_indices = df.index[any_anomaly].tolist()

    # Build anomalous records (limit to 50 for performance)
    records = []
    for idx in anomalous_indices[:50]:
        affected_cols = anomaly_mask.columns[anomaly_mask.loc[idx]].tolist()
        row_data = {}
        for col in df.columns[:10]:  # Limit columns in output
            val = df.at[idx, col]
            if pd.isna(val):
                row_data[col] = None
            elif isinstance(val, (np.integer, np.floating)):
                row_data[col] = round(float(val), 2)
            else:
                row_data[col] = str(val)
        records.append({
            "index": int(idx),
            "affected_columns": affected_cols,
            "data": row_data,
            "explanation": f"Potential anomaly in {', '.join(affected_cols)} — values outside expected IQR range.",
        })

    return {
        "method": "IQR (Interquartile Range)",
        "threshold": threshold,
        "total_anomalies": int(any_anomaly.sum()),
        "total_percentage": round(any_anomaly.sum() / len(df) * 100, 2) if len(df) > 0 else 0,
        "columns_analyzed": len(numeric_cols),
        "column_details": column_details,
        "anomalous_records": records,
    }


def _detect_zscore(df, numeric_cols, threshold=3.0):
    """Z-score based anomaly detection."""
    anomaly_mask = pd.DataFrame(False, index=df.index, columns=numeric_cols)
    column_details = []

    for col in numeric_cols:
        data = df[col].dropna()
        if len(data) < 10:
            continue

        mean = data.mean()
        std = data.std()
        if std == 0:
            continue

        z_scores = (df[col] - mean) / std
        mask = z_scores.abs() > threshold
        anomaly_mask[col] = mask
        count = int(mask.sum())

        if count > 0:
            column_details.append({
                "column": col,
                "method": "Z-score",
                "count": count,
                "percentage": round(count / len(df) * 100, 2),
                "mean": round(float(mean), 2),
                "std": round(float(std), 2),
                "threshold": threshold,
            })

    any_anomaly = anomaly_mask.any(axis=1)
    anomalous_indices = df.index[any_anomaly].tolist()

    records = []
    for idx in anomalous_indices[:50]:
        affected_cols = anomaly_mask.columns[anomaly_mask.loc[idx]].tolist()
        row_data = {}
        for col in df.columns[:10]:
            val = df.at[idx, col]
            if pd.isna(val):
                row_data[col] = None
            elif isinstance(val, (np.integer, np.floating)):
                row_data[col] = round(float(val), 2)
            else:
                row_data[col] = str(val)
        records.append({
            "index": int(idx),
            "affected_columns": affected_cols,
            "data": row_data,
            "explanation": f"Potential anomaly in {', '.join(affected_cols)} — Z-score exceeds ±{threshold}.",
        })

    return {
        "method": f"Z-score (threshold: ±{threshold})",
        "threshold": threshold,
        "total_anomalies": int(any_anomaly.sum()),
        "total_percentage": round(any_anomaly.sum() / len(df) * 100, 2) if len(df) > 0 else 0,
        "columns_analyzed": len(numeric_cols),
        "column_details": column_details,
        "anomalous_records": records,
    }


def _detect_isolation_forest(df, numeric_cols):
    """Isolation Forest multivariate anomaly detection."""
    try:
        from sklearn.ensemble import IsolationForest

        data = df[numeric_cols].dropna()
        if len(data) < 20:
            return {
                "method": "Isolation Forest",
                "total_anomalies": 0,
                "columns_analyzed": len(numeric_cols),
                "column_details": [],
                "anomalous_records": [],
                "message": "Insufficient data for Isolation Forest (need ≥20 complete rows).",
            }

        model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
        predictions = model.fit_predict(data)
        scores = model.decision_function(data)

        anomaly_mask = predictions == -1
        anomalous_indices = data.index[anomaly_mask].tolist()

        records = []
        for idx in anomalous_indices[:50]:
            row_data = {}
            for col in df.columns[:10]:
                val = df.at[idx, col]
                if pd.isna(val):
                    row_data[col] = None
                elif isinstance(val, (np.integer, np.floating)):
                    row_data[col] = round(float(val), 2)
                else:
                    row_data[col] = str(val)
            records.append({
                "index": int(idx),
                "affected_columns": numeric_cols,
                "anomaly_score": round(float(scores[data.index.get_loc(idx)]), 4),
                "data": row_data,
                "explanation": "Potential anomaly detected by Isolation Forest (multivariate analysis).",
            })

        return {
            "method": "Isolation Forest",
            "total_anomalies": int(anomaly_mask.sum()),
            "total_percentage": round(anomaly_mask.sum() / len(data) * 100, 2),
            "columns_analyzed": len(numeric_cols),
            "column_details": [],
            "anomalous_records": records,
        }
    except ImportError:
        return _detect_iqr(df, numeric_cols)
