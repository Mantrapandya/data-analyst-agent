"""AnalystFlow AI REST API Blueprint."""

import json
import os
import pandas as pd
from flask import Blueprint, request, jsonify, Response, current_app
from database import db
from models import Dataset
from config import Config
from services.file_service import validate_upload, parse_file, safe_filename, save_dataframe
from services.profiling_service import profile_dataset
from services.cleaning_service import detect_issues, apply_cleaning
from services.eda_service import generate_eda
from services.anomaly_service import detect_anomalies
from services.correlation_service import calculate_correlations
from services.insight_service import generate_business_insights
from services.sql_service import execute_sql_on_dataframe, validate_sql, SQLValidationError
from services.report_service import generate_executive_report
from services.export_service import export_cleaned_csv, export_analysis_json
from ai.analyst import generate_executive_narrative, ask_data

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _get_dataset_and_df(dataset_id, use_cleaned=True):
    """Retrieve dataset record and load its DataFrame."""
    dataset = db.session.get(Dataset, dataset_id)
    if not dataset:
        return None, None, "Dataset not found."

    file_to_load = dataset.cleaned_file_path if (use_cleaned and dataset.cleaned_file_path and os.path.exists(dataset.cleaned_file_path)) else dataset.file_path
    if not os.path.exists(file_to_load):
        return None, None, "Dataset file could not be located on disk."

    df, err = parse_file(file_to_load)
    if err:
        return dataset, None, err

    return dataset, df, None


# 1. Health Check
@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Data Analyst Agent",
        "version": "1.0.0",
        "ai_enabled": Config.ai_enabled(),
        "ai_provider": Config.AI_PROVIDER if Config.ai_enabled() else "offline_demo"
    })


# 2. File Upload
@api_bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request."}), 400

    file = request.files["file"]
    is_valid, err_msg = validate_upload(file)
    if not is_valid:
        return jsonify({"error": err_msg}), 400

    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    saved_name = safe_filename(file.filename)
    saved_path = os.path.join(Config.UPLOAD_FOLDER, saved_name)
    file.save(saved_path)

    # Parse and validate structure
    df, parse_err = parse_file(saved_path)
    if parse_err:
        if os.path.exists(saved_path):
            os.remove(saved_path)
        return jsonify({"error": f"Failed to process file: {parse_err}"}), 422

    # Auto profiling
    profile = profile_dataset(df)
    health_score = profile.get("health_score", 0)

    # Persist in DB
    dataset = Dataset(
        filename=saved_name,
        original_filename=file.filename,
        file_path=saved_path,
        file_size=os.path.getsize(saved_path),
        row_count=len(df),
        col_count=len(df.columns),
        status="profiled",
        health_score=health_score,
        profile_json=json.dumps(profile)
    )
    db.session.add(dataset)
    db.session.commit()

    return jsonify({
        "success": True,
        "dataset": dataset.to_dict(),
        "profile": profile
    }), 201


# 3. Load Sample Dataset (Multi-Dataset Support)
@api_bp.route("/sample", methods=["POST"])
def load_sample():
    req_data = request.get_json(silent=True) or {}
    sample_key = req_data.get("type", "sales").lower()

    sample_map = {
        "sales": ("sample_sales.csv", "Sample Sales Dataset"),
        "hr": ("sample_hr.csv", "Sample HR & Employee Dataset"),
        "real_estate": ("sample_real_estate.csv", "Sample Real Estate Dataset")
    }

    sample_filename, display_name = sample_map.get(sample_key, sample_map["sales"])
    sample_path = os.path.join(Config.SAMPLE_DATA_DIR, sample_filename)

    if not os.path.exists(sample_path):
        return jsonify({"error": f"Sample dataset file '{sample_filename}' is missing."}), 404

    # Copy sample to uploads
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    saved_name = safe_filename(sample_filename)
    saved_path = os.path.join(Config.UPLOAD_FOLDER, saved_name)

    with open(sample_path, "rb") as f_in, open(saved_path, "wb") as f_out:
        f_out.write(f_in.read())

    df, parse_err = parse_file(saved_path)
    if parse_err:
        return jsonify({"error": parse_err}), 500

    profile = profile_dataset(df)
    health_score = profile.get("health_score", 0)

    dataset = Dataset(
        filename=saved_name,
        original_filename=f"{sample_filename} ({display_name})",
        file_path=saved_path,
        file_size=os.path.getsize(saved_path),
        row_count=len(df),
        col_count=len(df.columns),
        status="profiled",
        health_score=health_score,
        profile_json=json.dumps(profile)
    )
    db.session.add(dataset)
    db.session.commit()

    return jsonify({
        "success": True,
        "dataset": dataset.to_dict(),
        "profile": profile
    }), 201


# 4. List Datasets
@api_bp.route("/datasets", methods=["GET"])
def list_datasets():
    datasets = Dataset.query.order_by(Dataset.created_at.desc()).all()
    return jsonify({"datasets": [d.to_dict() for d in datasets]})


# 5. Get Dataset Details & Profile
@api_bp.route("/datasets/<int:dataset_id>", methods=["GET"])
def get_dataset(dataset_id):
    dataset = db.get_or_404(Dataset, dataset_id)
    profile = json.loads(dataset.profile_json) if dataset.profile_json else None
    return jsonify({
        "dataset": dataset.to_dict(),
        "profile": profile
    })


# 6. Preview Dataset Rows
@api_bp.route("/datasets/<int:dataset_id>/preview", methods=["GET"])
def preview_data(dataset_id):
    limit = min(int(request.args.get("limit", 50)), 100)
    dataset, df, err = _get_dataset_and_df(dataset_id)
    if err:
        return jsonify({"error": err}), 400

    # Clean nan / inf for json
    preview_df = df.head(limit).copy()
    preview_df = preview_df.replace({float('nan'): None, float('inf'): None, float('-inf'): None})

    return jsonify({
        "columns": list(preview_df.columns),
        "data": preview_df.to_dict(orient="records"),
        "total_rows": len(df),
        "displayed_rows": len(preview_df),
        "is_cleaned": bool(dataset.cleaned_file_path)
    })


# 7. Cleaning Pipeline (Review or Apply)
@api_bp.route("/datasets/<int:dataset_id>/clean", methods=["POST", "GET"])
def clean_dataset(dataset_id):
    dataset = db.get_or_404(Dataset, dataset_id)
    # Always load original for clean operations
    df, err = parse_file(dataset.file_path)
    if err:
        return jsonify({"error": err}), 400

    req_json = request.get_json(silent=True) or {}
    if request.method == "GET" or req_json.get("mode") == "review":
        issues = detect_issues(df)
        return jsonify({
            "mode": "review",
            "detected_issues": issues,
            "total_issues": len(issues)
        })

    # Apply Safe Cleaning
    options = req_json.get("options", {})
    cleaned_df, changelog = apply_cleaning(df, options)

    # Save cleaned file separately
    cleaned_path = save_dataframe(cleaned_df, Config.UPLOAD_FOLDER, filename_prefix="cleaned")
    dataset.cleaned_file_path = cleaned_path
    dataset.cleaning_log = json.dumps(changelog)
    dataset.status = "cleaned"

    # Re-profile cleaned data
    new_profile = profile_dataset(cleaned_df)
    dataset.health_score = new_profile.get("health_score")
    dataset.profile_json = json.dumps(new_profile)
    dataset.row_count = len(cleaned_df)
    dataset.col_count = len(cleaned_df.columns)
    db.session.commit()

    return jsonify({
        "mode": "applied",
        "success": True,
        "changelog": changelog,
        "new_health_score": dataset.health_score,
        "dataset": dataset.to_dict(),
        "profile": new_profile
    })


# 8. Automated EDA Charts
@api_bp.route("/datasets/<int:dataset_id>/eda", methods=["GET"])
def get_eda(dataset_id):
    dataset, df, err = _get_dataset_and_df(dataset_id)
    if err:
        return jsonify({"error": err}), 400

    charts = generate_eda(df)
    return jsonify({
        "dataset_id": dataset_id,
        "total_charts": len(charts),
        "charts": charts
    })


# 9. Anomaly Detection
@api_bp.route("/datasets/<int:dataset_id>/anomalies", methods=["GET"])
def get_anomalies(dataset_id):
    method = request.args.get("method", "iqr")
    threshold = float(request.args.get("threshold", 1.5))
    dataset, df, err = _get_dataset_and_df(dataset_id)
    if err:
        return jsonify({"error": err}), 400

    result = detect_anomalies(df, method=method, threshold=threshold)
    return jsonify(result)


# 10. Correlation Analysis
@api_bp.route("/datasets/<int:dataset_id>/correlations", methods=["GET"])
def get_correlations(dataset_id):
    dataset, df, err = _get_dataset_and_df(dataset_id)
    if err:
        return jsonify({"error": err}), 400

    result = calculate_correlations(df)
    return jsonify(result)


# 11. Deterministic Insights + AI Narrative
@api_bp.route("/datasets/<int:dataset_id>/insights", methods=["GET"])
def get_insights(dataset_id):
    dataset, df, err = _get_dataset_and_df(dataset_id)
    if err:
        return jsonify({"error": err}), 400

    insights_data = generate_business_insights(df)
    profile = json.loads(dataset.profile_json) if dataset.profile_json else profile_dataset(df)
    anomalies = detect_anomalies(df, method="iqr")
    correlations = calculate_correlations(df)

    narrative = generate_executive_narrative(
        dataset.original_filename,
        profile,
        insights_data,
        anomalies,
        correlations
    )

    return jsonify({
        "kpis": insights_data.get("kpis", []),
        "deterministic_insights": insights_data.get("insights", []),
        "executive_highlights": insights_data.get("executive_highlights", []),
        "ai_narrative": narrative
    })


# 12. Ask Your Data
@api_bp.route("/datasets/<int:dataset_id>/ask", methods=["POST"])
def ask_question(dataset_id):
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Please provide a question."}), 400

    dataset, df, err = _get_dataset_and_df(dataset_id)
    if err:
        return jsonify({"error": err}), 400

    result = ask_data(df, question, dataset_name=dataset.original_filename)
    return jsonify(result)


# 13. Direct SQL Analyst Execution
@api_bp.route("/datasets/<int:dataset_id>/sql", methods=["POST"])
def execute_sql_query(dataset_id):
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query string is empty."}), 400

    dataset, df, err = _get_dataset_and_df(dataset_id)
    if err:
        return jsonify({"error": err}), 400

    try:
        result = execute_sql_on_dataframe(df, query)
        return jsonify(result)
    except SQLValidationError as e:
        return jsonify({"success": False, "error": str(e), "sql_used": query}), 403
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "sql_used": query}), 500


# 14. Executive Report Generation
@api_bp.route("/datasets/<int:dataset_id>/report", methods=["GET"])
def get_report(dataset_id):
    format_type = request.args.get("format", "html").lower()
    dataset, df, err = _get_dataset_and_df(dataset_id)
    if err:
        return jsonify({"error": err}), 400

    profile = json.loads(dataset.profile_json) if dataset.profile_json else profile_dataset(df)
    insights_data = generate_business_insights(df)
    anomalies = detect_anomalies(df, method="iqr")
    correlations = calculate_correlations(df)
    narrative = generate_executive_narrative(dataset.original_filename, profile, insights_data, anomalies, correlations)

    reports = generate_executive_report(dataset.to_dict(), profile, insights_data, anomalies, correlations, narrative)

    if format_type == "markdown":
        return Response(
            reports["markdown"],
            mimetype="text/markdown",
            headers={"Content-Disposition": f"attachment;filename=report_{dataset.id}.md"}
        )
    elif format_type == "html_download":
        return Response(
            reports["html"],
            mimetype="text/html",
            headers={"Content-Disposition": f"attachment;filename=report_{dataset.id}.html"}
        )

    return jsonify({
        "markdown": reports["markdown"],
        "html": reports["html"]
    })


# 15. Cleaned CSV Export
@api_bp.route("/datasets/<int:dataset_id>/export/csv", methods=["GET"])
def export_csv(dataset_id):
    dataset, df, err = _get_dataset_and_df(dataset_id)
    if err:
        return jsonify({"error": err}), 400

    csv_data = export_cleaned_csv(df)
    clean_name = f"cleaned_{dataset.original_filename.replace(' ', '_')}"
    if not clean_name.endswith(".csv"):
        clean_name += ".csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={clean_name}"}
    )


# 16. Full Analysis JSON Export
@api_bp.route("/datasets/<int:dataset_id>/export/json", methods=["GET"])
def export_json(dataset_id):
    dataset, df, err = _get_dataset_and_df(dataset_id)
    if err:
        return jsonify({"error": err}), 400

    profile = json.loads(dataset.profile_json) if dataset.profile_json else profile_dataset(df)
    insights = generate_business_insights(df)
    anomalies = detect_anomalies(df, method="iqr")
    correlations = calculate_correlations(df)

    json_data = export_analysis_json(dataset.to_dict(), profile, insights, anomalies, correlations)
    return Response(
        json_data,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename=analysis_{dataset.id}.json"}
    )
