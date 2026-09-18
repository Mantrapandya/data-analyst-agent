"""Generate multi-domain synthetic datasets for Data Analyst Agent.

Creates:
1. sample_sales.csv (E-Commerce / Sales transactions)
2. sample_hr.csv (Human Resources & Employee Performance)
3. sample_real_estate.csv (Housing & Real Estate Properties)
"""

import os
import random
import datetime

os.makedirs("sample_data", exist_ok=True)

# 1. SALES DATASET GENERATOR
def generate_sales_data():
    categories = {
        "Technology": [("Cloud Server Pro", 450.0, 270.0), ("Ultra Wireless Headset", 120.0, 65.0), ("Smart Data Hub 4K", 280.0, 160.0)],
        "Office Supplies": [("Copy Paper Case", 45.0, 25.0), ("Heavy Duty Shredder", 160.0, 95.0), ("Executive Gel Pens", 24.0, 9.0)],
        "Furniture": [("ErgoComfort Mesh Chair", 320.0, 190.0), ("Modular Conference Table", 890.0, 560.0), ("File Cabinet", 195.0, 115.0)]
    }
    regions = ["North America", "Europe", "Asia-Pacific", "Latin America"]
    first_names = ["James", "Emma", "Liam", "Olivia", "Noah", "Sophia", "Aarav", "Priya", "Carlos", "Yuki"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Patel", "Sharma", "Silva", "Sato", "Wong"]

    random.seed(42)
    customers = [(f"CUST-{i:04d}", f"{random.choice(first_names)} {random.choice(last_names)}") for i in range(1, 101)]

    records = []
    start_date = datetime.date(2023, 1, 1)

    for i in range(1, 801):
        order_id = f"ORD-{i:05d}"
        order_date = start_date + datetime.timedelta(days=random.randint(0, 500))
        cust_id, cust_name = random.choice(customers)
        category = random.choice(list(categories.keys()))
        product, base_price, base_cost = random.choice(categories[category])
        region = random.choice(regions)
        quantity = random.choices([1, 2, 3, 4, 5, 8], weights=[40, 25, 15, 10, 6, 4])[0]
        discount = random.choices([0.0, 0.05, 0.10, 0.15], weights=[60, 20, 12, 8])[0]

        unit_price = round(base_price * random.uniform(0.95, 1.05), 2)
        revenue = round(quantity * unit_price * (1.0 - discount), 2)
        cost = round(quantity * base_cost, 2)
        profit = round(revenue - cost, 2)

        records.append({
            "order_id": order_id,
            "order_date": order_date.strftime("%Y-%m-%d"),
            "customer_id": cust_id,
            "customer_name": cust_name,
            "product": product,
            "category": category,
            "region": region,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount": discount,
            "revenue": revenue,
            "cost": cost,
            "profit": profit
        })

    # Add minor outliers/missing values
    records[10]["discount"] = None
    records[45]["region"] = None
    records[120]["quantity"] = 95

    csv_path = os.path.join("sample_data", "sample_sales.csv")
    headers = ["order_id", "order_date", "customer_id", "customer_name", "product", "category", "region", "quantity", "unit_price", "discount", "revenue", "cost", "profit"]
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(",".join(headers) + "\n")
        for r in records:
            row = [str(r[h]) if r[h] is not None else "" for h in headers]
            f.write(",".join([f'"{v}"' if "," in v else v for v in row]) + "\n")

    print(f"[OK] Generated {len(records)} rows in {csv_path}")


# 2. HR DATASET GENERATOR
def generate_hr_data():
    departments = ["Engineering", "Sales", "Marketing", "Data Analytics", "Human Resources", "Finance", "Product"]
    job_titles = {
        "Engineering": ["Software Engineer", "Senior Developer", "DevOps Specialist", "QA Architect"],
        "Sales": ["Account Executive", "Sales Manager", "Business Development Rep"],
        "Marketing": ["Growth Marketer", "Content Strategist", "SEO Specialist"],
        "Data Analytics": ["Data Analyst", "Analytics Engineer", "Data Scientist", "BI Developer"],
        "Human Resources": ["HR Generalist", "Talent Recruiter", "People Operations Manager"],
        "Finance": ["Financial Analyst", "Staff Accountant", "Payroll Manager"],
        "Product": ["Product Manager", "UX Designer", "Technical Program Manager"]
    }
    locations = ["New York", "San Francisco", "Austin", "Remote", "London", "Toronto"]

    random.seed(101)
    records = []
    start_hire = datetime.date(2018, 1, 1)

    for i in range(1, 501):
        emp_id = f"EMP-{i:04d}"
        dept = random.choice(departments)
        role = random.choice(job_titles[dept])
        hire_date = start_hire + datetime.timedelta(days=random.randint(0, 2000))
        tenure_years = round((datetime.date(2024, 6, 1) - hire_date).days / 365.25, 1)
        location = random.choice(locations)

        # Base salary by department
        base_sal = {"Engineering": 115000, "Sales": 90000, "Marketing": 82000, "Data Analytics": 98000, "Human Resources": 75000, "Finance": 88000, "Product": 105000}[dept]
        salary = round(base_sal * (1 + (tenure_years * 0.04)) * random.uniform(0.9, 1.15), -2)
        performance_score = round(random.uniform(2.5, 5.0), 1)
        satisfaction_score = round(random.uniform(3.0, 5.0), 1)
        projects_completed = random.randint(2, 28)

        records.append({
            "employee_id": emp_id,
            "department": dept,
            "job_title": role,
            "location": location,
            "hire_date": hire_date.strftime("%Y-%m-%d"),
            "tenure_years": tenure_years,
            "salary": salary,
            "performance_score": performance_score,
            "satisfaction_score": satisfaction_score,
            "projects_completed": projects_completed
        })

    # Outlier salary
    records[15]["salary"] = 380000.0

    csv_path = os.path.join("sample_data", "sample_hr.csv")
    headers = ["employee_id", "department", "job_title", "location", "hire_date", "tenure_years", "salary", "performance_score", "satisfaction_score", "projects_completed"]
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(",".join(headers) + "\n")
        for r in records:
            row = [str(r[h]) if r[h] is not None else "" for h in headers]
            f.write(",".join([f'"{v}"' if "," in v else v for v in row]) + "\n")

    print(f"[OK] Generated {len(records)} rows in {csv_path}")


# 3. REAL ESTATE DATASET GENERATOR
def generate_real_estate_data():
    cities = ["Seattle", "Austin", "Denver", "Chicago", "Miami", "Boston", "Phoenix"]
    property_types = ["Single Family", "Condo", "Townhouse", "Multi-Family"]

    random.seed(202)
    records = []

    for i in range(1, 601):
        prop_id = f"PROP-{i:04d}"
        city = random.choice(cities)
        prop_type = random.choice(property_types)
        bedrooms = random.choices([1, 2, 3, 4, 5], weights=[10, 25, 35, 20, 10])[0]
        bathrooms = round(bedrooms * random.choice([0.75, 1.0, 1.25]), 1)
        sqft = int(bedrooms * random.uniform(450, 750))
        year_built = random.randint(1975, 2023)

        # Price per sqft based on city
        price_per_sqft = {"Seattle": 480, "Austin": 390, "Denver": 410, "Chicago": 280, "Miami": 520, "Boston": 550, "Phoenix": 310}[city]
        price = round(sqft * price_per_sqft * random.uniform(0.85, 1.2), -3)
        price_per_sqft_actual = round(price / sqft, 2)
        days_on_market = random.randint(4, 120)

        records.append({
            "property_id": prop_id,
            "city": city,
            "property_type": prop_type,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "square_feet": sqft,
            "year_built": year_built,
            "price": price,
            "price_per_sqft": price_per_sqft_actual,
            "days_on_market": days_on_market
        })

    csv_path = os.path.join("sample_data", "sample_real_estate.csv")
    headers = ["property_id", "city", "property_type", "bedrooms", "bathrooms", "square_feet", "year_built", "price", "price_per_sqft", "days_on_market"]
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(",".join(headers) + "\n")
        for r in records:
            row = [str(r[h]) if r[h] is not None else "" for h in headers]
            f.write(",".join([f'"{v}"' if "," in v else v for v in row]) + "\n")

    print(f"[OK] Generated {len(records)} rows in {csv_path}")


if __name__ == "__main__":
    generate_sales_data()
    generate_hr_data()
    generate_real_estate_data()
