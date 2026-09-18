"""In-memory Analytical SQL Engine with rigorous security sandboxing."""

import re
import sqlite3
import time
import pandas as pd
from services.column_detector import detect_column_roles


# Forbidden SQL tokens that could alter schema or state
FORBIDDEN_KEYWORDS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bTRUNCATE\b",
    r"\bATTACH\b",
    r"\bDETACH\b",
    r"\bPRAGMA\b",
    r"\bVACUUM\b",
    r"\bREINDEX\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
]


class SQLValidationError(Exception):
    pass


def validate_sql(query):
    """
    Ensure the SQL query is strictly read-only and harmless.
    Accepts SELECT and WITH...SELECT statements.
    Rejects any mutation or DDL.
    """
    clean_query = query.strip()
    # Strip comments
    clean_query = re.sub(r"--.*$", "", clean_query, flags=re.MULTILINE)
    clean_query = re.sub(r"/\*.*?\*/", "", clean_query, flags=re.DOTALL).strip()

    if not clean_query:
        raise SQLValidationError("Query is empty.")

    upper_query = clean_query.upper()

    # Must start with SELECT or WITH
    if not (upper_query.startswith("SELECT") or upper_query.startswith("WITH")):
        raise SQLValidationError("Only read-only SELECT queries are permitted.")

    # Check for forbidden keywords
    for pattern in FORBIDDEN_KEYWORDS:
        if re.search(pattern, upper_query):
            keyword = pattern.replace(r"\b", "")
            raise SQLValidationError(f"Security restriction: '{keyword}' statements are strictly disallowed.")

    # Check for multiple statements separated by semicolon
    statements = [s.strip() for s in clean_query.split(";") if s.strip()]
    if len(statements) > 1:
        raise SQLValidationError("Multiple statements are not permitted in a single query.")

    return clean_query


def execute_sql_on_dataframe(df, query, limit=500):
    """
    Load DataFrame into temporary SQLite database and execute read-only query.
    Returns:
        columns, rows, execution_time_ms, sql_used
    """
    sanitized_query = validate_sql(query)

    # If no LIMIT clause, append safe LIMIT
    if not re.search(r"\bLIMIT\b", sanitized_query, re.IGNORECASE):
        sanitized_query = f"{sanitized_query.rstrip(';')} LIMIT {limit}"

    # Clean column names for SQLite compatibility (replace spaces and symbols)
    sql_df = df.copy()
    original_cols = list(sql_df.columns)
    clean_col_map = {c: re.sub(r"[^\w]", "_", str(c)).strip("_") for c in original_cols}
    # Avoid collisions
    seen = {}
    final_cols = []
    for c in original_cols:
        clean = clean_col_map[c]
        if clean in seen:
            seen[clean] += 1
            final_cols.append(f"{clean}_{seen[clean]}")
        else:
            seen[clean] = 0
            final_cols.append(clean)
    sql_df.columns = final_cols

    start_time = time.time()
    conn = sqlite3.connect(":memory:")
    try:
        # Load dataset into in-memory table named 'dataset'
        sql_df.to_sql("dataset", conn, if_exists="replace", index=False)

        cursor = conn.cursor()
        cursor.execute(sanitized_query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        exec_time = round((time.time() - start_time) * 1000, 2)

        # Format rows for JSON serialization
        formatted_rows = []
        for row in rows:
            formatted_rows.append([
                None if v is None else (round(v, 4) if isinstance(v, float) else v)
                for v in row
            ])

        return {
            "success": True,
            "columns": columns,
            "rows": formatted_rows,
            "row_count": len(formatted_rows),
            "execution_time_ms": exec_time,
            "sql_used": sanitized_query,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
            "sql_used": sanitized_query,
            "error": str(e)
        }
    finally:
        conn.close()


def generate_heuristic_sql(df, user_question):
    """
    Deterministic rule-based SQL generator for Demo / Offline mode.
    Maps common analytical questions into precise, valid SQLite queries against 'dataset'.
    """
    q = user_question.lower().strip()
    roles = detect_column_roles(df)

    # Available columns mapped to sqlite clean names
    clean_col_map = {c: re.sub(r"[^\w]", "_", str(c)).strip("_") for c in df.columns}

    rev_col = next((clean_col_map[c] for c, r in roles.items() if r in ("revenue", "sales", "amount")), None)
    profit_col = next((clean_col_map[c] for c, r in roles.items() if r == "profit"), None)
    cat_col = next((clean_col_map[c] for c, r in roles.items() if r == "category"), None)
    reg_col = next((clean_col_map[c] for c, r in roles.items() if r == "region"), None)
    prod_col = next((clean_col_map[c] for c, r in roles.items() if r == "product"), None)
    cust_col = next((clean_col_map[c] for c, r in roles.items() if r in ("customer_name", "customer_id")), None)
    date_col = next((clean_col_map[c] for c, r in roles.items() if r == "date"), None)

    # Fallback first numeric / categorical column
    num_cols = [clean_col_map[c] for c in df.select_dtypes(include="number").columns]
    first_num = rev_col or (num_cols[0] if num_cols else None)

    cat_cols = [clean_col_map[c] for c in df.select_dtypes(include=["object", "category"]).columns]
    first_cat = cat_col or (cat_cols[0] if cat_cols else None)

    # 1. Top products
    if any(term in q for term in ["top product", "best selling product", "highest product"]):
        target_cat = prod_col or first_cat
        target_num = first_num
        if target_cat and target_num:
            return f"SELECT {target_cat}, ROUND(SUM({target_num}), 2) AS total_{target_num}, COUNT(*) AS transaction_count FROM dataset GROUP BY {target_cat} ORDER BY total_{target_num} DESC LIMIT 10;"

    # 2. Category analysis
    if any(term in q for term in ["category", "highest revenue category", "sales by category"]):
        target_cat = cat_col or first_cat
        target_num = first_num
        if target_cat and target_num:
            return f"SELECT {target_cat}, ROUND(SUM({target_num}), 2) AS total_{target_num}, ROUND(AVG({target_num}), 2) AS avg_{target_num} FROM dataset GROUP BY {target_cat} ORDER BY total_{target_num} DESC LIMIT 10;"

    # 3. Regional / Location analysis
    if any(term in q for term in ["region", "territory", "highest profit margin region", "location", "city", "state"]):
        target_cat = reg_col or first_cat
        target_num = profit_col or first_num
        if target_cat and target_num:
            return f"SELECT {target_cat}, ROUND(SUM({target_num}), 2) AS total_{target_num}, COUNT(*) AS total_records FROM dataset GROUP BY {target_cat} ORDER BY total_{target_num} DESC LIMIT 10;"

    # 4. Top customers
    if any(term in q for term in ["top 10 customer", "top customer", "customer spend", "best customer"]):
        target_cust = cust_col or first_cat
        target_num = first_num
        if target_cust and target_num:
            return f"SELECT {target_cust}, ROUND(SUM({target_num}), 2) AS total_spent, COUNT(*) AS orders_count FROM dataset GROUP BY {target_cust} ORDER BY total_spent DESC LIMIT 10;"

    # 5. Trend / Time analysis
    if any(term in q for term in ["over time", "trend", "month", "timeline", "sales over time"]):
        if date_col and first_num:
            return f"SELECT SUBSTR({date_col}, 1, 7) AS period, ROUND(SUM({first_num}), 2) AS total_{first_num}, COUNT(*) AS count FROM dataset GROUP BY period ORDER BY period ASC LIMIT 24;"

    # 6. Overall summary
    if any(term in q for term in ["summary", "total revenue", "overall", "total sales", "kpis"]):
        if rev_col and profit_col:
            return f"SELECT COUNT(*) AS total_records, ROUND(SUM({rev_col}), 2) AS total_revenue, ROUND(AVG({rev_col}), 2) AS avg_order_value, ROUND(SUM({profit_col}), 2) AS total_profit FROM dataset;"
        elif first_num:
            return f"SELECT COUNT(*) AS total_records, ROUND(SUM({first_num}), 2) AS total_{first_num}, ROUND(AVG({first_num}), 2) AS avg_{first_num}, ROUND(MIN({first_num}), 2) AS min_{first_num}, ROUND(MAX({first_num}), 2) AS max_{first_num} FROM dataset;"

    # Default general exploration
    if first_cat and first_num:
        return f"SELECT {first_cat}, COUNT(*) AS record_count, ROUND(SUM({first_num}), 2) AS total_{first_num} FROM dataset GROUP BY {first_cat} ORDER BY total_{first_num} DESC LIMIT 10;"
    
    # Generic top 10 preview
    return "SELECT * FROM dataset LIMIT 10;"
