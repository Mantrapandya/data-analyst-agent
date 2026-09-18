"""Automated EDA chart generation using Plotly."""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json


def generate_eda(df, roles=None):
    """Generate exploratory data analysis charts for the dataset.

    Returns a list of chart specs (Plotly JSON) with metadata.
    Only generates meaningful charts — skips low-value visualizations.
    """
    charts = []
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

    # 1. Distribution histograms for key numeric columns (max 6)
    for col in numeric_cols[:6]:
        if df[col].dropna().nunique() < 3:
            continue
        fig = px.histogram(
            df, x=col, nbins=30,
            title=f"Distribution of {col}",
            template="plotly_dark",
            color_discrete_sequence=["#6366f1"],
        )
        fig.update_layout(
            margin=dict(l=40, r=20, t=50, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e8eaed"),
            height=350,
        )
        charts.append({
            "id": f"hist_{col}",
            "type": "histogram",
            "title": f"Distribution of {col}",
            "column": col,
            "category": "distribution",
            "plotly_json": json.loads(fig.to_json()),
        })

    # 2. Box plots for numeric columns (max 6)
    for col in numeric_cols[:6]:
        if df[col].dropna().nunique() < 3:
            continue
        fig = px.box(
            df, y=col,
            title=f"Box Plot — {col}",
            template="plotly_dark",
            color_discrete_sequence=["#818cf8"],
        )
        fig.update_layout(
            margin=dict(l=40, r=20, t=50, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e8eaed"),
            height=350,
        )
        charts.append({
            "id": f"box_{col}",
            "type": "boxplot",
            "title": f"Box Plot — {col}",
            "column": col,
            "category": "distribution",
            "plotly_json": json.loads(fig.to_json()),
        })

    # 3. Bar charts for categorical columns (max 4, cardinality 2-30)
    for col in categorical_cols[:4]:
        nunique = df[col].dropna().nunique()
        if nunique < 2 or nunique > 30:
            continue
        value_counts = df[col].value_counts().head(15)
        fig = px.bar(
            x=value_counts.index.astype(str),
            y=value_counts.values,
            title=f"Frequency — {col}",
            template="plotly_dark",
            color_discrete_sequence=["#10b981"],
            labels={"x": col, "y": "Count"},
        )
        fig.update_layout(
            margin=dict(l=40, r=20, t=50, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e8eaed"),
            height=350,
        )
        charts.append({
            "id": f"bar_{col}",
            "type": "bar",
            "title": f"Frequency — {col}",
            "column": col,
            "category": "categorical",
            "plotly_json": json.loads(fig.to_json()),
        })

    # 4. Time series line charts
    for date_col in datetime_cols[:2]:
        # Find numeric columns to plot over time
        metric_cols = numeric_cols[:3]
        for metric_col in metric_cols:
            try:
                time_df = df[[date_col, metric_col]].dropna().copy()
                time_df = time_df.sort_values(date_col)
                # Resample to appropriate frequency
                time_df = time_df.set_index(date_col)
                range_days = (time_df.index.max() - time_df.index.min()).days
                if range_days > 365:
                    resampled = time_df.resample("MS").sum().reset_index()
                    freq_label = "Monthly"
                elif range_days > 60:
                    resampled = time_df.resample("W").sum().reset_index()
                    freq_label = "Weekly"
                else:
                    resampled = time_df.resample("D").sum().reset_index()
                    freq_label = "Daily"

                if len(resampled) < 3:
                    continue

                fig = px.line(
                    resampled, x=date_col, y=metric_col,
                    title=f"{freq_label} {metric_col} Trend",
                    template="plotly_dark",
                    color_discrete_sequence=["#f59e0b"],
                )
                fig.update_layout(
                    margin=dict(l=40, r=20, t=50, b=40),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e8eaed"),
                    height=350,
                )
                charts.append({
                    "id": f"trend_{metric_col}",
                    "type": "line",
                    "title": f"{freq_label} {metric_col} Trend",
                    "column": metric_col,
                    "category": "trends",
                    "plotly_json": json.loads(fig.to_json()),
                })
            except Exception:
                continue

    # 5. Category comparison (if category + numeric available)
    if categorical_cols and numeric_cols:
        cat_col = None
        for c in categorical_cols:
            n = df[c].dropna().nunique()
            if 2 <= n <= 15:
                cat_col = c
                break
        if cat_col:
            metric_col = numeric_cols[0]
            try:
                agg = df.groupby(cat_col)[metric_col].sum().sort_values(ascending=False).head(10)
                fig = px.bar(
                    x=agg.index.astype(str),
                    y=agg.values,
                    title=f"{metric_col} by {cat_col}",
                    template="plotly_dark",
                    color_discrete_sequence=["#ec4899"],
                    labels={"x": cat_col, "y": metric_col},
                )
                fig.update_layout(
                    margin=dict(l=40, r=20, t=50, b=40),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e8eaed"),
                    height=350,
                )
                charts.append({
                    "id": f"comparison_{cat_col}_{metric_col}",
                    "type": "bar",
                    "title": f"{metric_col} by {cat_col}",
                    "column": f"{cat_col},{metric_col}",
                    "category": "comparison",
                    "plotly_json": json.loads(fig.to_json()),
                })
            except Exception:
                pass

    # 6. Scatter plot of two most correlated numeric columns
    if len(numeric_cols) >= 2:
        try:
            corr = df[numeric_cols].corr().abs()
            np.fill_diagonal(corr.values, 0)
            max_idx = corr.stack().idxmax()
            col1, col2 = max_idx
            fig = px.scatter(
                df, x=col1, y=col2,
                title=f"Scatter — {col1} vs {col2}",
                template="plotly_dark",
                color_discrete_sequence=["#3b82f6"],
                opacity=0.6,
            )
            fig.update_layout(
                margin=dict(l=40, r=20, t=50, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8eaed"),
                height=350,
            )
            charts.append({
                "id": f"scatter_{col1}_{col2}",
                "type": "scatter",
                "title": f"Scatter — {col1} vs {col2}",
                "column": f"{col1},{col2}",
                "category": "correlation",
                "plotly_json": json.loads(fig.to_json()),
            })
        except Exception:
            pass

    return charts
