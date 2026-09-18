"""Test SQL analysis layer and security sandboxing."""

import pytest
from services.sql_service import validate_sql, execute_sql_on_dataframe, SQLValidationError


def test_sql_validator_allows_select():
    assert "SELECT * FROM dataset" in validate_sql("SELECT * FROM dataset")
    assert "WITH cte AS" in validate_sql("WITH cte AS (SELECT 1) SELECT * FROM cte")


def test_sql_validator_blocks_mutations():
    dangerous_queries = [
        "DROP TABLE dataset;",
        "DELETE FROM dataset WHERE 1=1;",
        "UPDATE dataset SET revenue = 0;",
        "INSERT INTO dataset VALUES (1);",
        "ALTER TABLE dataset ADD COLUMN hacked INT;",
        "SELECT * FROM dataset; DROP TABLE dataset;",
        "PRAGMA table_info(dataset);",
    ]
    for q in dangerous_queries:
        with pytest.raises(SQLValidationError):
            validate_sql(q)


def test_sql_execution(sample_dataframe):
    res = execute_sql_on_dataframe(sample_dataframe, "SELECT category, SUM(revenue) as total_rev FROM dataset GROUP BY category ORDER BY total_rev DESC")
    assert res["success"] is True
    assert len(res["rows"]) == 3
    assert res["columns"] == ["category", "total_rev"]
    assert res["execution_time_ms"] >= 0
