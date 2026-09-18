"""Safe data cleaning pipeline with detailed change tracking."""

import pandas as pd
import numpy as np


def detect_issues(df):
    """Detect data quality issues without modifying the DataFrame.

    Returns a list of detected issues with descriptions and affected columns.
    """
    issues = []

    # 1. Missing values
    missing = df.isnull().sum()
    cols_with_missing = missing[missing > 0]
    if len(cols_with_missing) > 0:
        for col, count in cols_with_missing.items():
            pct = round(count / len(df) * 100, 1)
            issues.append({
                "type": "missing_values",
                "column": col,
                "count": int(count),
                "percentage": pct,
                "description": f"Column '{col}' has {count} missing values ({pct}%).",
                "severity": "high" if pct > 30 else "medium" if pct > 10 else "low",
            })

    # 2. Duplicate rows
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        issues.append({
            "type": "duplicate_rows",
            "column": None,
            "count": dup_count,
            "percentage": round(dup_count / len(df) * 100, 1),
            "description": f"Found {dup_count} duplicate rows.",
            "severity": "medium",
        })

    # 3. Whitespace issues in string columns
    for col in df.select_dtypes(include="object").columns:
        ws_count = 0
        non_null = df[col].dropna()
        if len(non_null) > 0:
            stripped = non_null.str.strip()
            ws_count = int((non_null != stripped).sum())
        if ws_count > 0:
            issues.append({
                "type": "whitespace",
                "column": col,
                "count": ws_count,
                "percentage": round(ws_count / len(df) * 100, 1),
                "description": f"Column '{col}' has {ws_count} values with leading/trailing whitespace.",
                "severity": "low",
            })

    # 4. Numeric values stored as strings
    for col in df.select_dtypes(include="object").columns:
        non_null = df[col].dropna()
        if len(non_null) > 0:
            numeric_count = pd.to_numeric(non_null, errors="coerce").notna().sum()
            if numeric_count > len(non_null) * 0.8 and numeric_count > 5:
                issues.append({
                    "type": "numeric_as_string",
                    "column": col,
                    "count": int(numeric_count),
                    "percentage": round(numeric_count / len(non_null) * 100, 1),
                    "description": f"Column '{col}' appears numeric but is stored as text ({numeric_count} values).",
                    "severity": "medium",
                })

    # 5. Constant columns
    for col in df.columns:
        if df[col].dropna().nunique() <= 1 and len(df[col].dropna()) > 0:
            issues.append({
                "type": "constant_column",
                "column": col,
                "count": 1,
                "percentage": 100,
                "description": f"Column '{col}' has only one unique value.",
                "severity": "low",
            })

    return issues


def apply_cleaning(df, options=None):
    """Apply safe cleaning transformations to a copy of the DataFrame.

    Never modifies the original. Returns (cleaned_df, changelog).

    Options dict can include:
    - remove_duplicates: bool (default True)
    - strip_whitespace: bool (default True)
    - convert_numeric: bool (default True)
    - fill_missing_numeric: str "median"|"mean"|"zero"|"drop" (default "median")
    - fill_missing_categorical: str "mode"|"unknown"|"drop" (default "mode")
    """
    if options is None:
        options = {}

    cleaned = df.copy()
    changelog = []

    # 1. Remove duplicates
    if options.get("remove_duplicates", True):
        before = len(cleaned)
        cleaned = cleaned.drop_duplicates()
        removed = before - len(cleaned)
        if removed > 0:
            changelog.append(f"Removed {removed} duplicate rows.")

    # 2. Strip whitespace from string columns
    if options.get("strip_whitespace", True):
        ws_fixed = 0
        for col in cleaned.select_dtypes(include="object").columns:
            non_null = cleaned[col].dropna()
            if len(non_null) > 0:
                stripped = non_null.str.strip()
                changed = (non_null != stripped).sum()
                if changed > 0:
                    cleaned[col] = cleaned[col].str.strip()
                    ws_fixed += int(changed)
        if ws_fixed > 0:
            changelog.append(f"Stripped whitespace from {ws_fixed} values.")

    # 3. Convert numeric-like string columns
    if options.get("convert_numeric", True):
        converted_cols = []
        for col in cleaned.select_dtypes(include="object").columns:
            non_null = cleaned[col].dropna()
            if len(non_null) > 0:
                numeric_converted = pd.to_numeric(non_null, errors="coerce")
                if numeric_converted.notna().sum() > len(non_null) * 0.8:
                    cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")
                    converted_cols.append(col)
        if converted_cols:
            changelog.append(f"Converted {len(converted_cols)} columns to numeric: {', '.join(converted_cols)}.")

    # 4. Fill missing values in numeric columns
    fill_numeric = options.get("fill_missing_numeric", "median")
    numeric_cols = cleaned.select_dtypes(include="number").columns
    filled_numeric = 0
    for col in numeric_cols:
        missing_count = cleaned[col].isnull().sum()
        if missing_count > 0:
            if fill_numeric == "median":
                fill_val = cleaned[col].median()
                cleaned[col] = cleaned[col].fillna(fill_val)
            elif fill_numeric == "mean":
                fill_val = cleaned[col].mean()
                cleaned[col] = cleaned[col].fillna(fill_val)
            elif fill_numeric == "zero":
                cleaned[col] = cleaned[col].fillna(0)
            elif fill_numeric == "drop":
                cleaned = cleaned.dropna(subset=[col])
            filled_numeric += int(missing_count)
    if filled_numeric > 0 and fill_numeric != "drop":
        changelog.append(f"Filled {filled_numeric} missing numeric values using {fill_numeric} strategy.")

    # 5. Fill missing values in categorical columns
    fill_cat = options.get("fill_missing_categorical", "mode")
    cat_cols = cleaned.select_dtypes(include=["object", "category"]).columns
    filled_cat = 0
    for col in cat_cols:
        missing_count = cleaned[col].isnull().sum()
        if missing_count > 0:
            if fill_cat == "mode":
                mode_val = cleaned[col].mode()
                if len(mode_val) > 0:
                    cleaned[col] = cleaned[col].fillna(mode_val.iloc[0])
            elif fill_cat == "unknown":
                cleaned[col] = cleaned[col].fillna("Unknown")
            elif fill_cat == "drop":
                cleaned = cleaned.dropna(subset=[col])
            filled_cat += int(missing_count)
    if filled_cat > 0 and fill_cat != "drop":
        changelog.append(f"Filled {filled_cat} missing categorical values using {fill_cat} strategy.")

    # Reset index
    cleaned = cleaned.reset_index(drop=True)

    if not changelog:
        changelog.append("No issues found. Dataset is already clean.")

    return cleaned, changelog
