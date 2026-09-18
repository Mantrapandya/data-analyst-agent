import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32).hex())
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    SAMPLE_DATA_DIR = os.path.join(BASE_DIR, "sample_data")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "50")) * 1024 * 1024

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'analystflow.db')}")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AI Configuration (optional)
    AI_PROVIDER = os.getenv("AI_PROVIDER", "")  # "openai" or "gemini"
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "")

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    @classmethod
    def ai_enabled(cls):
        return bool(cls.AI_PROVIDER and cls.AI_API_KEY)
