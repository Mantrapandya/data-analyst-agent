"""AnalystFlow AI — Autonomous AI Data Analyst Platform.

Single entry point for development and production.
Run with: python app.py
"""

import os
import sys
import socket
from flask import Flask, render_template, send_from_directory, jsonify
from flask.json.provider import DefaultJSONProvider
import numpy as np
from config import Config
from database import db, init_db
from api.routes import api_bp
from models import Dataset


class NumpyJSONProvider(DefaultJSONProvider):
    """Custom JSON provider capable of serializing NumPy types."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def create_app():
    """Application factory for AnalystFlow AI."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static"
    )
    app.config.from_object(Config)
    app.json = NumpyJSONProvider(app)

    # Initialize extensions
    db.init_app(app)

    # Register API blueprint
    app.register_blueprint(api_bp)

    # Ensure required directories exist
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.SAMPLE_DATA_DIR, exist_ok=True)

    # Initialize database tables
    with app.app_context():
        init_db(app)

    # Main Web UI Route
    @app.route("/")
    def index():
        return render_template("index.html")

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found."}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error occurred.", "details": str(e)}), 500

    return app


app = create_app()


def find_available_port(preferred_port=5000, max_attempts=20):
    """Find an open port starting from preferred_port."""
    for port in range(preferred_port, preferred_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return preferred_port


if __name__ == "__main__":
    port = find_available_port(preferred_port=5000)
    host = "127.0.0.1"

    print("\n" + "=" * 60)
    print("   ANALYSTFLOW AI — AUTONOMOUS AI DATA ANALYST")
    print("   'Turn raw data into decisions.'")
    print("=" * 60)
    print(f"\n   Local URL: http://{host}:{port}")
    print(f"   API Health: http://{host}:{port}/api/health\n")
    print("=" * 60 + "\n")

    # Disable reloader to prevent duplicate subprocesses on Windows
    app.run(host=host, port=port, debug=False, use_reloader=False)
