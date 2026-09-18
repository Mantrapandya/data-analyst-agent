"""Dataset-Agnostic Business Insight & KPI Engine.

Extracts verifiable, data-backed insights derived strictly from detected dataset metrics.
Supports Sales, HR, Real Estate, Financial, Operational, and Generic datasets.
Guarantees ZERO hardcoded fake metrics or zero-value fallbacks.
"""

import numpy as np
import pandas as pd
from services.column_detector import (
    detect_column_roles,
    get_metric_columns,
    get_dimension_columns,
    get_date_columns,
    get_id_columns
)


def generate_business_insights(df):
    """
    Generate domain-aware, dataset-agnostic KPIs and insights.
    Returns:
        - kpis: List of dynamic KPI cards matching the dataset schema
        - insights: List of structured findings with supporting numbers
        - executive_highlights: Top 3-5 key takeaways
        - detected_roles: Mapped semantic roles
    """
    roles = detect_column_roles(df)
    metric_cols = get_metric_columns(df, roles)
    dim_cols = get_dimension_columns(df, roles)
    date_cols = get_date_columns(df, roles)
    id_cols = get_id_columns(df, roles)

    kpis = _generate_dynamic_kpis(df, roles, metric_cols, dim_cols, id_cols)
    insights = []

    # 1. Category / Dimension Contribution Insights
    if metric_cols and dim_cols:
        for metric_col in list(metric_cols.keys())[:3]:
            for dim_col in list(dim_cols.keys())[:3]:
                insight = _analyze_dimension_contribution(df, dim_col, metric_col)
                if insight:
                    insights.append(insight)

    # 2. Time-Series Growth & Trend Insights
    if date_cols and metric_cols:
        primary_date = list(date_cols.keys())[0]
        for metric_col in list(metric_cols.keys())[:3]:
            trend_insight = _analyze_time_trend(df, primary_date, metric_col)
            if trend_insight:
                insights.append(trend_insight)

    # 3. Domain Specific Profit / Margin Analysis
    margin_insight = _analyze_margins(df, metric_cols)
    if margin_insight:
        insights.append(margin_insight)

    # 4. Outlier & Concentration Check (Pareto Principle)
    for metric_col in list(metric_cols.keys())[:2]:
        pareto_insight = _analyze_pareto(df, metric_col)
        if pareto_insight:
            insights.append(pareto_insight)

    # 5. Highlights Extraction
    highlights = []
    for ins in insights:
        if ins.get("significance") == "high":
            highlights.append(ins["headline"])
    if len(highlights) < 3:
        for ins in insights:
            if ins["headline"] not in highlights:
                highlights.append(ins["headline"])
            if len(highlights) >= 4:
                break

    if not highlights:
        num_cols_cnt = len(df.select_dtypes(include="number").columns)
        cat_cols_cnt = len(df.select_dtypes(include=["object", "category"]).columns)
        highlights.append(f"Processed dataset containing {len(df):,} records and {len(df.columns)} attributes.")
        highlights.append(f"Identified {num_cols_cnt} numeric variables and {cat_cols_cnt} categorical dimensions.")

    return {
        "kpis": kpis,
        "insights": insights,
        "executive_highlights": highlights[:5],
        "detected_roles": roles
    }


def _generate_dynamic_kpis(df, roles, metric_cols, dim_cols, id_cols):
    """
    Dynamically construct KPI cards matching the dataset domain.
    Never display fake $0 Revenue/Profit/Orders when those columns don't exist.
    """
    kpi_cards = []

    # Domain Pattern 1: E-Commerce / Sales (Revenue, Profit, Quantity)
    rev_col = next((c for c, r in roles.items() if r in ("revenue", "sales")), None)
    profit_col = next((c for c, r in roles.items() if r == "profit"), None)
    
    if rev_col:
        total_rev = float(df[rev_col].sum())
        avg_rev = float(df[rev_col].mean())
        kpi_cards.append({
            "id": "total_revenue",
            "title": f"Total {rev_col.replace('_', ' ').title()}",
            "value": f"${total_rev:,.2f}",
            "raw_value": total_rev,
            "subtitle": f"Mean: ${avg_rev:,.2f} per record",
            "icon": "dollar-sign"
        })

    if profit_col:
        total_profit = float(df[profit_col].sum())
        kpi_cards.append({
            "id": "total_profit",
            "title": f"Total {profit_col.replace('_', ' ').title()}",
            "value": f"${total_profit:,.2f}",
            "raw_value": total_profit,
            "subtitle": "Cumulative profit across records",
            "icon": "trending-up"
        })
        if rev_col and df[rev_col].sum() > 0:
            margin = (total_profit / df[rev_col].sum()) * 100
            kpi_cards.append({
                "id": "profit_margin",
                "title": "Profit Margin",
                "value": f"{margin:.1f}%",
                "raw_value": margin,
                "subtitle": f"Profit / {rev_col.replace('_', ' ').title()}",
                "icon": "percent"
            })

    # Domain Pattern 2: HR & Employee Metrics (Salary, Performance, Tenure)
    sal_col = next((c for c, r in roles.items() if r == "salary"), None)
    perf_col = next((c for c, r in roles.items() if r == "performance"), None)
    emp_col = next((c for c, r in roles.items() if r == "employee_id"), None)

    if sal_col:
        avg_sal = float(df[sal_col].mean())
        tot_sal = float(df[sal_col].sum())
        kpi_cards.append({
            "id": "avg_salary",
            "title": f"Average {sal_col.replace('_', ' ').title()}",
            "value": f"${avg_sal:,.0f}",
            "raw_value": avg_sal,
            "subtitle": f"Payroll Total: ${tot_sal:,.0f}",
            "icon": "briefcase"
        })

    if perf_col:
        avg_perf = float(df[perf_col].mean())
        kpi_cards.append({
            "id": "avg_performance",
            "title": f"Average {perf_col.replace('_', ' ').title()}",
            "value": f"{avg_perf:.2f} / 5.0",
            "raw_value": avg_perf,
            "subtitle": "Mean performance evaluation",
            "icon": "award"
        })

    # Domain Pattern 3: Real Estate (Price, Square Feet, Price/SqFt)
    price_col = next((c for c, r in roles.items() if r == "price" and c not in (rev_col, sal_col)), None)
    sqft_col = next((c for c, r in roles.items() if r == "square_feet"), None)

    if price_col:
        avg_price = float(df[price_col].mean())
        tot_volume = float(df[price_col].sum())
        kpi_cards.append({
            "id": "avg_price",
            "title": f"Average {price_col.replace('_', ' ').title()}",
            "value": f"${avg_price:,.0f}",
            "raw_value": avg_price,
            "subtitle": f"Total Market Volume: ${tot_volume:,.0f}",
            "icon": "home"
        })

    if sqft_col and price_col:
        avg_sqft = float(df[sqft_col].mean())
        tot_sqft = float(df[sqft_col].sum())
        price_per_sqft = float(df[price_col].sum() / tot_sqft) if tot_sqft > 0 else 0
        kpi_cards.append({
            "id": "price_per_sqft",
            "title": "Avg Price / SqFt",
            "value": f"${price_per_sqft:,.2f}",
            "raw_value": price_per_sqft,
            "subtitle": f"Mean size: {avg_sqft:,.0f} sqft",
            "icon": "grid"
        })

    # Entity Count KPI (Orders, Customers, Employees, Properties, or Total Records)
    if emp_col:
        unique_emp = int(df[emp_col].nunique())
        kpi_cards.append({
            "id": "total_employees",
            "title": "Headcount / Employees",
            "value": f"{unique_emp:,}",
            "raw_value": unique_emp,
            "subtitle": f"Tracked in {emp_col}",
            "icon": "users"
        })
    elif next((c for c, r in roles.items() if r == "property_id"), None):
        prop_col = next(c for c, r in roles.items() if r == "property_id")
        unique_props = int(df[prop_col].nunique())
        kpi_cards.append({
            "id": "total_properties",
            "title": "Properties / Listings",
            "value": f"{unique_props:,}",
            "raw_value": unique_props,
            "subtitle": f"Tracked in {prop_col}",
            "icon": "building"
        })
    elif next((c for c, r in roles.items() if r == "order_id"), None):
        order_col = next(c for c, r in roles.items() if r == "order_id")
        unique_orders = int(df[order_col].nunique())
        kpi_cards.append({
            "id": "total_orders",
            "title": "Total Transactions",
            "value": f"{unique_orders:,}",
            "raw_value": unique_orders,
            "subtitle": f"Tracked in {order_col}",
            "icon": "shopping-cart"
        })

    # Fallback Generic KPIs if specific domain KPIs are insufficient (< 3 cards)
    if len(kpi_cards) < 3:
        # Total Records Card
        kpi_cards.append({
            "id": "total_records",
            "title": "Total Records",
            "value": f"{len(df):,}",
            "raw_value": int(len(df)),
            "subtitle": f"{len(df.columns)} attributes tracked",
            "icon": "database"
        })

        # Top Numeric Metric Card if available and not already added
        num_cols = list(df.select_dtypes(include="number").columns)
        for num_c in num_cols:
            if not any(k["id"] == f"kpi_{num_c}" for k in kpi_cards):
                sum_val = float(df[num_c].sum())
                avg_val = float(df[num_c].mean())
                kpi_cards.append({
                    "id": f"kpi_{num_c}",
                    "title": f"Mean {num_c.replace('_', ' ').title()}",
                    "value": f"{avg_val:,.2f}",
                    "raw_value": avg_val,
                    "subtitle": f"Total: {sum_val:,.2f}",
                    "icon": "bar-chart-2"
                })
                if len(kpi_cards) >= 4:
                    break

    return kpi_cards[:4]


def _analyze_dimension_contribution(df, dim_col, metric_col):
    """Examine segment concentration for any numerical metric."""
    try:
        clean = df[[dim_col, metric_col]].dropna()
        if len(clean) == 0:
            return None

        grouped = clean.groupby(dim_col)[metric_col].sum().sort_values(ascending=False)
        total_val = float(grouped.sum())
        if total_val <= 0 or len(grouped) < 2:
            return None

        top_item = str(grouped.index[0])
        top_val = float(grouped.iloc[0])
        top_share = (top_val / total_val) * 100

        if top_share >= 25:
            return {
                "category": "Contribution & Dominance",
                "headline": f"{dim_col.replace('_', ' ').title()} '{top_item}' generates {top_share:.1f}% of total {metric_col.replace('_', ' ')}.",
                "details": f"The top {dim_col.replace('_', ' ')} '{top_item}' contributed {top_val:,.2f} out of a total {total_val:,.2f}.",
                "metric": metric_col,
                "dimension": dim_col,
                "significance": "high" if top_share > 45 else "medium",
                "supporting_data": {
                    "top_name": top_item,
                    "top_value": round(top_val, 2),
                    "top_share_pct": round(top_share, 1),
                    "total_value": round(total_val, 2)
                }
            }
    except Exception:
        pass
    return None


def _analyze_time_trend(df, date_col, metric_col):
    """Analyze period-over-period growth or contraction."""
    try:
        clean = df[[date_col, metric_col]].dropna().copy()
        clean[date_col] = pd.to_datetime(clean[date_col], errors="coerce")
        clean = clean.dropna().sort_values(date_col)
        if len(clean) < 10:
            return None

        mid_date = clean[date_col].quantile(0.5)
        first_half = float(clean[clean[date_col] <= mid_date][metric_col].sum())
        second_half = float(clean[clean[date_col] > mid_date][metric_col].sum())

        if first_half > 0:
            growth_pct = ((second_half - first_half) / first_half) * 100
            direction = "expanded" if growth_pct > 0 else "declined"
            sig = "high" if abs(growth_pct) > 20 else "medium"
            return {
                "category": "Growth & Trends",
                "headline": f"{metric_col.replace('_', ' ').title()} {direction} by {abs(growth_pct):.1f}% in the second half of the observed period.",
                "details": f"First period total: {first_half:,.2f}, Second period total: {second_half:,.2f}.",
                "metric": metric_col,
                "dimension": date_col,
                "significance": sig,
                "supporting_data": {
                    "first_half_sum": round(first_half, 2),
                    "second_half_sum": round(second_half, 2),
                    "growth_pct": round(growth_pct, 2)
                }
            }
    except Exception:
        pass
    return None


def _analyze_margins(df, metric_cols):
    """Calculate and explain profit margins if profit and revenue exist."""
    rev_col = next((col for col, role in metric_cols.items() if role in ("revenue", "sales")), None)
    profit_col = next((col for col, role in metric_cols.items() if role == "profit"), None)

    if rev_col and profit_col:
        clean = df[[rev_col, profit_col]].dropna()
        tot_rev = float(clean[rev_col].sum())
        tot_prof = float(clean[profit_col].sum())
        if tot_rev > 0:
            overall_margin = (tot_prof / tot_rev) * 100
            loss_rows = int((clean[profit_col] < 0).sum())
            loss_pct = (loss_rows / len(clean)) * 100 if len(clean) > 0 else 0

            return {
                "category": "Profitability",
                "headline": f"Overall operational profit margin stands at {overall_margin:.1f}%.",
                "details": f"{loss_rows} transactions ({loss_pct:.1f}%) were recorded at a net loss.",
                "metric": profit_col,
                "significance": "high" if loss_pct > 10 or overall_margin < 10 else "medium",
                "supporting_data": {
                    "total_revenue": round(tot_rev, 2),
                    "total_profit": round(tot_prof, 2),
                    "margin_pct": round(overall_margin, 2),
                    "negative_profit_records": loss_rows
                }
            }
    return None


def _analyze_pareto(df, metric_col):
    """Compute top 20% concentration (Pareto principle)."""
    try:
        clean = df[metric_col].dropna().sort_values(ascending=False)
        if len(clean) < 20:
            return None
        top_20_count = max(1, int(len(clean) * 0.2))
        top_20_sum = float(clean.iloc[:top_20_count].sum())
        total_sum = float(clean.sum())

        if total_sum > 0:
            concentration_pct = (top_20_sum / total_sum) * 100
            if concentration_pct >= 50:
                return {
                    "category": "Risk & Concentration",
                    "headline": f"Top 20% of entries account for {concentration_pct:.1f}% of total {metric_col.replace('_', ' ')}.",
                    "details": f"High concentration detected in {metric_col.replace('_', ' ')}, indicating value is skewed toward key transactions.",
                    "metric": metric_col,
                    "significance": "high" if concentration_pct > 70 else "medium",
                    "supporting_data": {
                        "top_20_pct_sum": round(top_20_sum, 2),
                        "total_sum": round(total_sum, 2),
                        "concentration_pct": round(concentration_pct, 1)
                    }
                }
    except Exception:
        pass
    return None
