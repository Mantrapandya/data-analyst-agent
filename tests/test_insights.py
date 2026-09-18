"""Test deterministic business insight generation and dynamic KPIs."""

from services.insight_service import generate_business_insights


def test_business_insights_generation(sample_dataframe):
    result = generate_business_insights(sample_dataframe)
    
    assert "kpis" in result
    assert len(result["kpis"]) >= 3
    # Check that total revenue was computed
    rev_kpi = next((k for k in result["kpis"] if "Revenue" in k["title"]), None)
    assert rev_kpi is not None
    assert rev_kpi["raw_value"] == float(sample_dataframe["revenue"].sum())

    # Check profit margin
    margin_kpi = next((k for k in result["kpis"] if "Margin" in k["title"]), None)
    assert margin_kpi is not None
    assert margin_kpi["raw_value"] > 0

    assert "executive_highlights" in result
