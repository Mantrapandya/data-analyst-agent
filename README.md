# Data Analyst Agent — Your Autonomous AI Data Analyst

> **"Your Autonomous AI Data Analyst"**

Data Analyst Agent is a production-grade, end-to-end autonomous data analytics platform designed to demonstrate modern Data Analyst and Analytics Engineering workflows. Users can upload tabular data (CSV/Excel), inspect an automated multi-factor Data Health Score, review and apply safe cleaning transformations, explore interactive EDA charts, conduct statistical anomaly detection, inspect correlation heatmaps, query their data using sandboxed SQL or natural language, and generate executive-ready business intelligence reports.

---

## 🌟 Why This Project Demonstrates Core Data Analyst Skills

| Skill | Implementation in Data Analyst Agent |
| :--- | :--- |
| **Python & Data Engineering** | Modular architecture built with Python 3, Flask, SQLAlchemy, Pandas, and NumPy. |
| **Data Profiling & Quality** | Deterministic 5-pillar Data Health Score (Completeness, Uniqueness, Consistency, Validity, Richness). |
| **Data Cleaning** | Safe cleaning pipeline with changelog audit trail; preserves original data and creates versioned cleaned datasets. |
| **Exploratory Data Analysis (EDA)** | Intelligent auto-generation of distribution histograms, box plots, time-series trends, and category comparisons. |
| **Statistical Analysis** | Robust Interquartile Range (IQR), Z-score outlier detection, and Pearson correlation matrices. |
| **Interactive Visualization** | Reactive analytical dashboards powered by Plotly.js for zoom, pan, and hover inspections. |
| **SQL Mastery & Sandboxing** | In-memory SQLite analytics engine executing safe, read-only SELECT queries with keyword sandboxing. |
| **Business Intelligence** | Deterministic insight extraction (Pareto 80/20 concentration, margin analysis, customer repeat metrics). |
| **AI Augmentation & Guardrails** | Generative synthesis over pre-computed metrics to prevent mathematical hallucinations. Full offline mode. |
| **Automation & Reporting** | Instant executive report compilation in HTML and Markdown with KPI cards and recommendations. |

---

## 🏗️ Architecture & Data Flow

```
                                  [ Upload CSV / Excel ]
                                             │
                                             ▼
                                 [ File Validation & Parsing ]
                                 (Encoding, Dates, Headers)
                                             │
                                             ▼
                                  [ Data Profiling Engine ]
                           (5-Pillar Data Health Score: 0-100)
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
             [ Safe Cleaning Pipeline ]                  [ Automated EDA Engine ]
          (Review & Versioned Clean Data)          (Distributions, Boxplots, Trends)
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             ▼
                                [ Analytics & Insights ]
                       ┌─────────────────────┼─────────────────────┐
                       ▼                     ▼                     ▼
             [ Statistical Anomalies ] [ Correlation Matrix ] [ Business Insights ]
               (IQR & Z-score bounds)     (Pearson & Heatmap)    (KPIs & Pareto)
                                             │
                                             ▼
                                 [ Analytical SQL Engine ]
                            (In-memory SQLite Read-Only Sandbox)
                                             │
                                             ▼
                                  [ AI Analyst Layer ]
                             (Grounded in verified metrics)
                        Mode 1: Pure Offline Deterministic Analysis
                        Mode 2: Enhanced LLM (OpenAI / Gemini)
                                             │
                                             ▼
                               [ Executive Report & Export ]
                         (HTML Report, Markdown, Cleaned CSV, JSON)
```

---

## 🚀 Key Features

### 1. Transparent Data Health Score
Scored on a scale of 0–100 with clear, documented methodology:
- **Completeness (30 pts)**: Penalizes missing data cells across columns.
- **Uniqueness (20 pts)**: Penalizes duplicate row ratios.
- **Consistency (20 pts)**: Penalizes constant columns and mixed types.
- **Validity (15 pts)**: Penalizes extreme outlier density.
- **Richness (15 pts)**: Rewards datasets containing balanced numeric, categorical, and temporal attributes.

### 2. Non-Destructive Safe Cleaning
- **Issue Audit**: Scans for missing values, whitespace, numeric strings, and duplicates.
- **Review Mode**: View exact transformations before applying.
- **Apply Mode**: Generates a versioned cleaned file, leaving the raw uploaded data untouched.
- **Changelog**: Detailed audit log showing exact row removals and column conversions.

### 3. Automated Exploratory Data Analysis (EDA)
- Selects visualizations intelligently (avoids high-cardinality noise).
- Distribution histograms with adaptive binning.
- Outlier box plots for numerical dispersion.
- Frequency bar charts for categorical metrics.
- Temporal aggregation (Daily / Weekly / Monthly resampled trends).

### 4. Statistical Anomaly & Outlier Surveillance
- Multi-method detection: **IQR (Interquartile Range)** and **Z-Score**.
- Contextual anomaly explanations specifying lower/upper bounds and affected variables.
- Flags records without assuming fraud (uses neutral language: *"Potential anomaly detected"*).

### 5. Correlation Matrix & Association Heatmap
- Computes pairwise Pearson correlation coefficients.
- Renders dynamic Plotly heatmaps with color-coded associations.
- Explicitly communicates: *"Correlation measures statistical association, not cause and effect."*

### 6. Sandboxed Analytical SQL Layer
- Tabular data is mounted into an in-memory SQLite table (`dataset`).
- **Security Sandboxing**: Strictly disallows `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `ATTACH`, `PRAGMA`.
- Displays **"SQL Used"** so analysts and interviewers can audit the exact query.

### 7. Dual-Mode "Ask Your Data"
- **Mode 1 (Offline / Demo)**: Pure deterministic heuristics translating questions into SQL and calculating precise figures.
- **Mode 2 (AI-Enhanced)**: Natural language reasoning powered by OpenAI or Google Gemini, strictly grounded in verified metrics.

### 8. Executive Report Generator
- Produces structured business reports with Executive Summary, KPIs, Data Quality, Discoveries, Outliers, and Recommendations.
- Exportable as standalone **HTML** and GitHub-flavored **Markdown**.

---

## 📦 Project Structure

```
analystflow-ai/
├── app.py                     # Main server entrypoint & port resolver
├── config.py                  # Pydantic-style configuration & environment loader
├── database.py                # SQLAlchemy database connection
├── models.py                  # Dataset ORM model
├── generate_sample.py         # Realistic 1,000-row synthetic sales data generator
├── requirements.txt           # Production dependencies
├── .env.example               # Environment template
├── .gitignore                 # Git ignore configuration
│
├── api/
│   ├── __init__.py
│   └── routes.py              # Flask Blueprint with all REST endpoints
│
├── services/
│   ├── __init__.py
│   ├── column_detector.py     # Semantic column role detection
│   ├── file_service.py        # File validation, CSV/XLSX parsing
│   ├── profiling_service.py   # Statistical profiling & Data Health scoring
│   ├── cleaning_service.py    # Non-destructive cleaning pipeline
│   ├── eda_service.py         # Automated Plotly chart generator
│   ├── anomaly_service.py     # Statistical outlier detection (IQR, Z-Score)
│   ├── correlation_service.py # Pearson correlation matrix & heatmap
│   ├── insight_service.py     # Deterministic business KPIs & Pareto insights
│   ├── sql_service.py         # Sandboxed SQLite execution engine
│   ├── report_service.py      # Executive report generator (HTML/Markdown)
│   └── export_service.py      # Export utilities (CSV, JSON)
│
├── ai/
│   ├── __init__.py
│   ├── provider.py            # Abstract base class for LLMs
│   ├── openai_provider.py     # Pure Python OpenAI client
│   ├── gemini_provider.py     # Pure Python Google Gemini client
│   └── analyst.py             # Grounded AI synthesis orchestrator
│
├── static/
│   ├── css/
│   │   └── styles.css         # Modern SaaS dark-mode stylesheet
│   └── js/
│       └── app.js             # Frontend reactive application controller
│
├── templates/
│   └── index.html             # Semantic single-page application dashboard
│
├── sample_data/
│   └── sample_sales.csv       # 1,000 synthetic transaction records
│
└── tests/
    ├── conftest.py            # Test fixtures & in-memory test database
    ├── test_health.py         # Health endpoint test
    ├── test_upload.py         # File upload & validation tests
    ├── test_profiling.py      # Profiling & health score tests
    ├── test_cleaning.py       # Safe cleaning pipeline tests
    ├── test_eda.py            # EDA chart generation tests
    ├── test_anomaly.py        # Anomaly detection tests
    ├── test_correlation.py    # Correlation analysis tests
    ├── test_insights.py       # Dynamic KPI tests
    ├── test_sql.py            # SQL sandboxing and execution tests
    ├── test_reports.py        # Executive report compilation tests
    └── test_smoke.py          # End-to-end integration test
```

---

## ⚡ Zero-Friction Setup & Quickstart

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)

### 1. One-Command Launch
```bash
# From workspace root:
python app.py
```

The application will:
1. Automatically bind to an available local port (`http://127.0.0.1:5000`).
2. Initialize the SQLite database and create tables.
3. Serve the web application.

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

Click **"Try Sample Dataset"** to immediately explore the platform using 1,000 pre-generated transaction records.

---

## 🧪 Running Automated Tests

Run the complete test suite:

```bash
python -m pytest tests/ -v
```

All 16 unit, service, and end-to-end integration tests execute in under 2 seconds.

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/health` | `GET` | Health check and system readiness status. |
| `/api/upload` | `POST` | Upload and automatically profile CSV or Excel files. |
| `/api/sample` | `POST` | Load the 1,000-row synthetic sales dataset. |
| `/api/datasets` | `GET` | List all uploaded and processed datasets. |
| `/api/datasets/<id>` | `GET` | Retrieve dataset metadata and full profile. |
| `/api/datasets/<id>/preview` | `GET` | View tabular records with pagination. |
| `/api/datasets/<id>/clean` | `POST` | Audit issues (`mode=review`) or apply safe clean (`mode=apply`). |
| `/api/datasets/<id>/eda` | `GET` | Retrieve automated Plotly chart specifications. |
| `/api/datasets/<id>/anomalies` | `GET` | Execute statistical outlier detection (IQR or Z-Score). |
| `/api/datasets/<id>/correlations`| `GET` | Compute correlation matrix and heatmap. |
| `/api/datasets/<id>/insights` | `GET` | Generate dynamic KPIs, Pareto metrics, and executive summary. |
| `/api/datasets/<id>/ask` | `POST` | Natural language question answering with validated SQL. |
| `/api/datasets/<id>/sql` | `POST` | Direct read-only SQL query execution. |
| `/api/datasets/<id>/report` | `GET` | Generate HTML or Markdown executive report. |
| `/api/datasets/<id>/export/csv` | `GET` | Download cleaned dataset as CSV. |
| `/api/datasets/<id>/export/json`| `GET` | Download complete structured analysis payload as JSON. |

---

## 🔒 Security & Sandboxing
- **Read-Only SQL Enforcement**: Queries are validated against a strict whitelist allowing only `SELECT` and `WITH ... SELECT` queries. Mutating operations (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`) are rejected before execution.
- **No Client Arbitrary Code Execution**: Python scripts are never accepted from external user input or AI generation.
- **Secret Isolation**: API keys are accessed solely via environment variables and never logged or serialized in exports.

---

## 📄 License
This project is open-source under the MIT License.
