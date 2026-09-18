"""Test executive report generation."""

from services.profiling_service import profile_dataset
from services.insight_service import generate_business_insights
from services.anomaly_service import detect_anomalies
from services.correlation_service import calculate_correlations
from services.report_service import generate_executive_report


def test_executive_report_generation(sample_dataframe):
    dataset_dict = {
        "id": 1,
        "filename": "sample_sales.csv",
        "original_filename": "sample_sales.csv",
        "health_score": 92
    }
    profile = profile_dataset(sample_dataframe)
    insights = generate_business_insights(sample_dataframe)
    anomalies = detect_anomalies(sample_dataframe)
    correlations = calculate_correlations(sample_dataframe)

    reports = generate_executive_report(dataset_dict, profile, insights, anomalies, correlations)
    
    assert "markdown" in reports
    assert "html" in reports
    assert "# Executive Analytical Report" in reports["markdown"]
    assert "<!DOCTYPE html>" in reports["html"]
    assert "Data Health" in reports["html"]
