"""AI Data Analyst Orchestration Layer.

Combines deterministic metrics, SQL querying, and LLM synthesis.
Guarantees full analytical functionality in Offline / Demo Mode.
"""

import json
from config import Config
from ai.openai_provider import OpenAIProvider
from ai.gemini_provider import GeminiProvider
from services.sql_service import execute_sql_on_dataframe, generate_heuristic_sql


def get_ai_provider():
    """Instantiate configured AI provider or None."""
    provider_name = (Config.AI_PROVIDER or "").lower().strip()
    api_key = Config.AI_API_KEY or ""

    if provider_name == "openai":
        return OpenAIProvider(api_key=api_key, model=Config.AI_MODEL or "gpt-4o-mini")
    elif provider_name == "gemini":
        return GeminiProvider(api_key=api_key, model=Config.AI_MODEL or "gemini-1.5-flash")
    return None


def generate_executive_narrative(dataset_name, profile, insights_data, anomalies_data, correlations_data):
    """
    Generate an AI executive narrative based strictly on computed metrics.
    If AI is disabled, returns high-quality deterministic narrative.
    """
    provider = get_ai_provider()
    
    # Check if provider is available and configured
    if not provider or not provider.is_configured():
        # Fallback to rich deterministic summary
        overview = profile.get("overview", {})
        health_score = profile.get("health_score", 0)
        highlights = insights_data.get("executive_highlights", [])
        
        summary_text = (
            f"Automated evaluation of dataset '{dataset_name}' across {overview.get('rows', 0):,} records "
            f"and {overview.get('columns', 0)} attributes indicates a composite Data Health Score of {health_score}/100. "
            f"The dataset features {overview.get('numeric_columns', 0)} numeric and {overview.get('categorical_columns', 0)} categorical dimensions. "
            f"Statistical anomaly analysis flagged {anomalies_data.get('total_anomalies', 0):,} potential outlier events ({anomalies_data.get('total_percentage', 0)}% of total rows)."
        )

        findings = []
        for ins in insights_data.get("insights", [])[:4]:
            findings.append(f"{ins['headline']} {ins['details']}")

        recommendations = [
            "Validate and isolate records containing missing or anomalous values before feeding into downstream production systems.",
            "Establish automated continuous monitoring for high-concentration dimensions to mitigate single-category dependence.",
            "Integrate deeper cohort tracking to monitor retention and repeat engagement over quarterly periods."
        ]

        return {
            "mode": "deterministic",
            "executive_summary": summary_text,
            "key_findings": findings,
            "opportunities": [
                "Segment cross-selling: Focus promotional inventory on top performing categories.",
                "Process optimization: Address loss-making transactions through minimum order value policies."
            ],
            "risks": [
                f"{anomalies_data.get('total_percentage', 0)}% of entries exhibit significant variance or outlier traits.",
                "Concentration risk: High reliance on top contributing categories or accounts."
            ],
            "recommendations": recommendations,
            "note": "AI-enhanced synthesis is running in offline demo mode. To enable LLM narratives, configure AI_API_KEY in settings or environment."
        }

    # AI is configured: build structured, grounded prompt
    system_prompt = (
        "You are Data Analyst Agent, an Autonomous AI Data Analyst and Business Intelligence Expert. "
        "Strict Rule: Rely ONLY on the provided verified metrics. Do NOT fabricate numbers, metrics, or company names. "
        "If evidence is not present in the data, state 'Insufficient evidence in dataset'. "
        "Deliver clear, concise executive insights."
    )

    metrics_payload = {
        "dataset_name": dataset_name,
        "overview": profile.get("overview"),
        "quality": profile.get("quality"),
        "health_score": profile.get("health_score"),
        "kpis": insights_data.get("kpis"),
        "top_insights": [i["headline"] for i in insights_data.get("insights", [])[:5]],
        "anomalies_count": anomalies_data.get("total_anomalies"),
        "anomalies_pct": anomalies_data.get("total_percentage"),
        "correlations": [f"{c['column_1']} & {c['column_2']}: {c['correlation']}" for c in correlations_data.get("top_positive", [])[:3]]
    }

    prompt = (
        f"Analyze the following verified dataset metrics and produce a structured JSON summary:\n"
        f"{json.dumps(metrics_payload, indent=2)}\n\n"
        "Return a valid JSON object with keys: "
        "'executive_summary' (string), 'key_findings' (array of strings), "
        "'opportunities' (array of strings), 'risks' (array of strings), 'recommendations' (array of strings)."
    )

    response_text = provider.generate_text(prompt, system_prompt)

    try:
        # Extract json from markdown block if needed
        clean_text = response_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
        parsed = json.loads(clean_text)
        parsed["mode"] = "ai_enhanced"
        return parsed
    except Exception:
        return {
            "mode": "ai_enhanced",
            "executive_summary": response_text[:500],
            "key_findings": [response_text[:300]],
            "opportunities": [],
            "risks": [],
            "recommendations": [],
            "raw": response_text
        }


def ask_data(df, question, dataset_name="dataset"):
    """
    End-to-end 'Ask Your Data' execution pipeline:
    Question -> Intent / SQL Generation -> SQL Sandbox Execution -> Result Validation -> Explanation
    """
    provider = get_ai_provider()
    
    # 1. Generate SQL query
    if provider and provider.is_configured():
        col_list = [f"{c} ({str(df[c].dtype)})" for c in df.columns]
        system_prompt = (
            "You are an expert SQL analyst. Generate a single read-only SQLite SELECT query against table 'dataset'. "
            "Never use DROP, DELETE, INSERT, UPDATE, ALTER, CREATE. "
            "Return ONLY the SQL query without markdown or explanation."
        )
        prompt = (
            f"Table: dataset\n"
            f"Columns: {', '.join(col_list)}\n\n"
            f"User Question: {question}\n\n"
            f"SQLite Query:"
        )
        ai_sql = provider.generate_text(prompt, system_prompt).strip()
        # Clean any backticks
        ai_sql = ai_sql.replace("```sql", "").replace("```", "").strip()
        sql_query = ai_sql if ai_sql.upper().startswith("SELECT") else generate_heuristic_sql(df, question)
    else:
        sql_query = generate_heuristic_sql(df, question)

    # 2. Execute SQL query safely
    exec_result = execute_sql_on_dataframe(df, sql_query)

    # 3. Generate explanation
    if not exec_result["success"]:
        return {
            "question": question,
            "sql_used": exec_result["sql_used"],
            "execution_time_ms": exec_result["execution_time_ms"],
            "error": exec_result["error"],
            "answer": f"Could not execute query: {exec_result['error']}",
            "data": None
        }

    # Generate answer explanation
    if provider and provider.is_configured():
        explain_prompt = (
            f"User Question: {question}\n"
            f"SQL Query: {exec_result['sql_used']}\n"
            f"Result Columns: {exec_result['columns']}\n"
            f"Result Rows (sample): {exec_result['rows'][:10]}\n\n"
            "Provide a concise, direct business answer citing the specific numbers. Do not fabricate."
        )
        answer = provider.generate_text(explain_prompt, "You are a concise data analyst. Answer directly with numbers.")
    else:
        # Deterministic formatting
        cols = exec_result["columns"]
        rows = exec_result["rows"]
        if not rows:
            answer = "The query returned zero matching records."
        elif len(rows) == 1 and len(cols) == 1:
            val = rows[0][0]
            answer = f"The resulting {cols[0]} is **{val:,}**." if isinstance(val, (int, float)) else f"Result: **{val}**."
        elif len(rows) == 1:
            parts = [f"**{c}**: {v:,.2f}" if isinstance(v, float) else f"**{c}**: {v}" for c, v in zip(cols, rows[0])]
            answer = f"Summary Metrics: {', '.join(parts)}."
        else:
            top_row = rows[0]
            answer = (
                f"Query completed with {len(rows)} results. "
                f"Leading entry: {cols[0]} '{top_row[0]}' with {cols[1] if len(cols) > 1 else 'value'} = {top_row[1] if len(top_row) > 1 else 'N/A'}."
            )

    return {
        "question": question,
        "sql_used": exec_result["sql_used"],
        "execution_time_ms": exec_result["execution_time_ms"],
        "columns": exec_result["columns"],
        "rows": exec_result["rows"][:50],  # Return up to 50 preview rows
        "total_rows_returned": len(exec_result["rows"]),
        "answer": answer,
        "mode": "ai_enhanced" if (provider and provider.is_configured()) else "local_analyst"
    }
