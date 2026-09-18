"""Pytest fixtures for AnalystFlow AI."""

import os
import tempfile
import pytest
import pandas as pd
from app import create_app
from database import db
from models import Dataset


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    test_app = create_app()
    test_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for HTTP requests."""
    return app.test_client()


@pytest.fixture
def sample_dataframe():
    """Create a realistic sample DataFrame for testing."""
    data = {
        "order_id": ["ORD-01", "ORD-02", "ORD-03", "ORD-04", "ORD-05"],
        "order_date": ["2024-01-10", "2024-01-15", "2024-02-01", "2024-02-18", "2024-03-05"],
        "customer_id": ["C-101", "C-102", "C-101", "C-103", "C-104"],
        "category": ["Technology", "Furniture", "Technology", "Office Supplies", "Technology"],
        "region": ["North", "South", "North", "West", "East"],
        "quantity": [2, 1, 5, 10, 3],
        "unit_price": [100.0, 250.0, 100.0, 15.0, 120.0],
        "discount": [0.0, 0.1, 0.05, 0.0, 0.15],
        "revenue": [200.0, 225.0, 475.0, 150.0, 306.0],
        "cost": [120.0, 150.0, 250.0, 80.0, 180.0],
        "profit": [80.0, 75.0, 225.0, 70.0, 126.0],
    }
    return pd.DataFrame(data)
