"""Semantic column detection for automatic KPI and metric identification across any dataset."""

import re

# Mapping of semantic roles to likely column name patterns
COLUMN_PATTERNS = {
    # Financial / Sales
    "revenue": [r"revenue", r"total_sales", r"sales_amount", r"gross_sales", r"income"],
    "sales": [r"sales", r"units_sold", r"quantity_sold"],
    "amount": [r"amount", r"total", r"sum", r"val", r"value"],
    "price": [r"\bprice\b", r"unit_price", r"rate", r"msrp", r"cost_price"],
    "cost": [r"\bcost\b", r"cogs", r"expense", r"spending"],
    "profit": [r"profit", r"margin", r"net_income", r"earnings"],
    "quantity": [r"quantity", r"qty", r"units", r"volume"],
    "discount": [r"discount", r"rebate", r"reduction"],

    # HR & Employee Metrics
    "salary": [r"salary", r"pay", r"wage", r"compensation"],
    "performance": [r"performance", r"score", r"rating", r"evaluation"],
    "satisfaction": [r"satisfaction", r"engagement", r"morale"],
    "tenure": [r"tenure", r"years_at_company", r"service_years"],
    "employee_id": [r"employee_id", r"emp_id", r"staff_id"],
    "department": [r"department", r"dept", r"team", r"division"],

    # Real Estate & Property Metrics
    "square_feet": [r"square_feet", r"sqft", r"area_sqft", r"size"],
    "bedrooms": [r"bedrooms", r"beds", r"bed_count"],
    "bathrooms": [r"bathrooms", r"baths", r"bath_count"],
    "year_built": [r"year_built", r"built_year", r"construction_year"],
    "days_on_market": [r"days_on_market", r"dom", r"listing_days"],
    "property_id": [r"property_id", r"prop_id", r"listing_id", r"parcel"],

    # Common IDs & Dimensions
    "customer_id": [r"customer_id", r"cust_id", r"client_id", r"buyer_id"],
    "customer_name": [r"customer_name", r"cust_name", r"client_name", r"buyer_name", r"customer"],
    "order_id": [r"order_id", r"order_no", r"transaction_id", r"invoice"],
    "product": [r"product", r"item", r"sku", r"product_name"],
    "category": [r"category", r"segment", r"group", r"class", r"property_type"],
    "region": [r"region", r"territory", r"area", r"zone", r"location", r"city", r"state", r"country"],
    "date": [r"date", r"order_date", r"hire_date", r"transaction_date", r"timestamp", r"time"],
    "status": [r"status", r"condition", r"stage"],
}


def detect_column_roles(df):
    """Detect semantic roles for each column in the DataFrame."""
    roles = {}
    col_names_lower = {col: col.lower().strip().replace(" ", "_") for col in df.columns}

    for col, col_lower in col_names_lower.items():
        for role, patterns in COLUMN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, col_lower):
                    roles[col] = role
                    break
            if col in roles:
                break

    return roles


def get_metric_columns(df, roles):
    """Identify numeric columns suitable for metric calculations."""
    metric_roles = {
        "revenue", "sales", "amount", "price", "cost", "profit", "quantity", "discount",
        "salary", "performance", "satisfaction", "tenure", "square_feet", "bedrooms",
        "bathrooms", "year_built", "days_on_market"
    }
    result = {col: role for col, role in roles.items() if role in metric_roles}
    
    # Include all remaining numeric columns if not explicitly assigned an ID role
    id_roles = {"customer_id", "order_id", "employee_id", "property_id"}
    for col in df.select_dtypes(include="number").columns:
        if col not in result and roles.get(col) not in id_roles:
            result[col] = "numeric_metric"
    return result


def get_dimension_columns(df, roles):
    """Identify columns suitable for categorical breakdown."""
    dimension_roles = {"category", "region", "product", "customer_name", "department", "status"}
    result = {col: role for col, role in roles.items() if role in dimension_roles}
    
    for col in df.select_dtypes(include=["object", "category"]).columns:
        if col not in result and col not in roles:
            nunique = df[col].nunique()
            if 2 <= nunique <= 60:
                result[col] = "category"
    return result


def get_date_columns(df, roles):
    """Identify datetime columns."""
    result = {col: role for col, role in roles.items() if role == "date"}
    for col in df.select_dtypes(include=["datetime64"]).columns:
        if col not in result:
            result[col] = "date"
    return result


def get_id_columns(df, roles):
    """Identify identifier columns."""
    id_roles = {"customer_id", "order_id", "employee_id", "property_id"}
    return {col: role for col, role in roles.items() if role in id_roles}
