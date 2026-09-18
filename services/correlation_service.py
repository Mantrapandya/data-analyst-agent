"""Correlation analysis engine with statistical validation."""

import numpy as np
import pandas as pd
import json
import plotly.graph_objects as go


def calculate_correlations(df, method="pearson", min_periods=5):
    """
    Calculate correlation matrix and extract significant relationships.
    Reminds the user: Correlation does not imply causation.
    """
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    if len(numeric_cols) < 2:
        return {
            "matrix": {},
            "columns": numeric_cols,
            "top_positive": [],
            "top_negative": [],
            "total_pairs": 0,
            "message": "At least two numeric columns are required to calculate correlation.",
            "disclaimer": "Notice: Correlation measures statistical association, not cause and effect.",
            "heatmap_json": None,
        }

    # Compute correlation matrix
    corr_df = df[numeric_cols].corr(method=method, min_periods=min_periods)
    
    # Clean NaN/Inf in matrix
    corr_df = corr_df.fillna(0.0)

    # Build matrix dict
    matrix_dict = {}
    for col in numeric_cols:
        matrix_dict[col] = {
            other_col: round(float(corr_df.loc[col, other_col]), 4)
            for other_col in numeric_cols
        }

    # Extract pairs
    pairs = []
    seen = set()
    for i in range(len(numeric_cols)):
        for j in range(i + 1, len(numeric_cols)):
            col1 = numeric_cols[i]
            col2 = numeric_cols[j]
            val = float(corr_df.loc[col1, col2])
            if not np.isnan(val) and not np.isinf(val):
                pairs.append({
                    "column_1": col1,
                    "column_2": col2,
                    "correlation": round(val, 4),
                    "strength": _interpret_strength(val),
                })

    # Sort positive and negative
    positive_pairs = sorted([p for p in pairs if p["correlation"] > 0], key=lambda x: x["correlation"], reverse=True)
    negative_pairs = sorted([p for p in pairs if p["correlation"] < 0], key=lambda x: x["correlation"])

    # Generate Plotly heatmap
    heatmap_json = None
    try:
        z_vals = [[round(float(corr_df.loc[r, c]), 2) for c in numeric_cols] for r in numeric_cols]
        fig = go.Figure(data=go.Heatmap(
            z=z_vals,
            x=numeric_cols,
            y=numeric_cols,
            colorscale='RdBu_r',
            zmin=-1,
            zmax=1,
            text=z_vals,
            texttemplate="%{text}",
            textfont={"size": 11, "color": "#ffffff"},
            colorbar=dict(title="Correlation")
        ))
        fig.update_layout(
            title="Correlation Matrix Heatmap",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e8eaed"),
            height=min(550, max(380, len(numeric_cols) * 45)),
            margin=dict(l=60, r=40, t=50, b=60)
        )
        heatmap_json = json.loads(fig.to_json())
    except Exception:
        heatmap_json = None

    return {
        "columns": numeric_cols,
        "matrix": matrix_dict,
        "top_positive": positive_pairs[:8],
        "top_negative": negative_pairs[:8],
        "total_pairs": len(pairs),
        "disclaimer": "Statistical Note: Correlation measures association strength between variables, not direct causation.",
        "heatmap_json": heatmap_json
    }


def _interpret_strength(val):
    abs_val = abs(val)
    if abs_val >= 0.8:
        return "Very Strong"
    elif abs_val >= 0.6:
        return "Strong"
    elif abs_val >= 0.4:
        return "Moderate"
    elif abs_val >= 0.2:
        return "Weak"
    return "Very Weak"
