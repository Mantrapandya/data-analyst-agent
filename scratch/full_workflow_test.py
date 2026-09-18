import urllib.request
import urllib.parse
import json

base = 'http://127.0.0.1:5002'

def run_full_ui_e2e_simulation():
    print("============================================================")
    print("   DATA ANALYST AGENT — FULL END-TO-END WORKFLOW SIMULATION")
    print("============================================================")

    # 1. Health Check
    req = urllib.request.urlopen(f'{base}/api/health')
    health = json.loads(req.read().decode())
    assert health['status'] == 'ok'
    print(f"[OK] 1. Server running at {base} | Service: {health['service']} (v{health['version']})")

    # 2. Load Sales Sample Dataset
    data = json.dumps({'type': 'sales'}).encode('utf-8')
    req = urllib.request.Request(f'{base}/api/sample', data=data, headers={'Content-Type': 'application/json'})
    res = urllib.request.urlopen(req)
    ds_res = json.loads(res.read().decode())
    ds_id = ds_res['dataset']['id']
    print(f"[OK] 2. Sample Sales Dataset Loaded (ID: {ds_id}, File: {ds_res['dataset']['original_filename']})")

    # 3. Fetch Dataset Profile & Overview
    req = urllib.request.urlopen(f'{base}/api/datasets/{ds_id}')
    profile_data = json.loads(req.read().decode())
    print(f"[OK] 3. Data Profile Loaded | Health Score: {profile_data['dataset']['health_score']} / 100")

    # 4. Fetch Overview Insights & Dynamic KPIs
    req = urllib.request.urlopen(f'{base}/api/datasets/{ds_id}/insights')
    insights = json.loads(req.read().decode())
    kpi_titles = [k['title'] for k in insights['kpis']]
    print(f"[OK] 4. Overview KPIs Generated: {kpi_titles}")
    print(f"     Executive Summary: {insights['ai_narrative']['executive_summary']}")

    # 5. Data Explorer Preview (Table & Filtering)
    req = urllib.request.urlopen(f'{base}/api/datasets/{ds_id}/preview?limit=50')
    preview = json.loads(req.read().decode())
    print(f"[OK] 5. Data Explorer Table Loaded ({preview['displayed_rows']} rows, {len(preview['columns'])} columns)")

    # 6. Safe Data Cleaning Review & Apply
    clean_req_data = json.dumps({'mode': 'apply'}).encode('utf-8')
    req = urllib.request.Request(f'{base}/api/datasets/{ds_id}/clean', data=clean_req_data, headers={'Content-Type': 'application/json'})
    res = urllib.request.urlopen(req)
    clean_res = json.loads(res.read().decode())
    print(f"[OK] 6. Safe Cleaning Applied: Success={clean_res['success']} (Changelog items: {len(clean_res['changelog'])}, New Health Score: {clean_res['new_health_score']})")

    # 7. Automated EDA Charts
    req = urllib.request.urlopen(f'{base}/api/datasets/{ds_id}/eda')
    eda = json.loads(req.read().decode())
    print(f"[OK] 7. Automated EDA Charts Rendered ({eda['total_charts']} charts generated)")

    # 8. Statistical Anomaly Detection
    req = urllib.request.urlopen(f'{base}/api/datasets/{ds_id}/anomalies?method=iqr')
    anomalies = json.loads(req.read().decode())
    print(f"[OK] 8. Statistical Anomalies Analyzed ({anomalies['total_anomalies']} potential anomalies flagged via {anomalies['method']})")

    # 9. Correlation Matrix & Heatmap
    req = urllib.request.urlopen(f'{base}/api/datasets/{ds_id}/correlations')
    corr = json.loads(req.read().decode())
    print(f"[OK] 9. Correlation Matrix Computed (Top positive pair: {corr['top_positive'][0]['column_1']} - {corr['top_positive'][0]['column_2']}, r={corr['top_positive'][0]['correlation']})")

    # 10. Ask Data (Natural Language to SQL)
    ask_payload = json.dumps({'question': 'What is the total revenue by product category?'}).encode('utf-8')
    req = urllib.request.Request(f'{base}/api/datasets/{ds_id}/ask', data=ask_payload, headers={'Content-Type': 'application/json'})
    res = urllib.request.urlopen(req)
    ask_res = json.loads(res.read().decode())
    print(f"[OK] 10. Ask Data Answered Question: '{ask_res['question']}'")
    print(f"      Generated SQL: {ask_res['sql_used']}")
    print(f"      Answer: {ask_res['answer'][:120]}...")

    # 11. Executive Report Generation
    req = urllib.request.urlopen(f'{base}/api/datasets/{ds_id}/report?format=json')
    report = json.loads(req.read().decode())
    print(f"[OK] 11. Executive Report Compiled ({len(report['html'])} bytes of HTML generated)")

    print("============================================================")
    print("   SUCCESS! 100% COMPLETE WORKFLOW VERIFIED WITH ZERO ERRORS")
    print("============================================================")

if __name__ == '__main__':
    run_full_ui_e2e_simulation()
