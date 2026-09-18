from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app=None):
    """Create all tables. Called at app startup."""
    if app:
        with app.app_context():
            db.create_all()
    else:
        db.create_all()
