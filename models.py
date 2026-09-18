import datetime
from database import db


class Dataset(db.Model):
    """Represents an uploaded dataset and its analysis state."""

    __tablename__ = "datasets"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    cleaned_file_path = db.Column(db.String(512), nullable=True)
    file_size = db.Column(db.Integer, default=0)
    row_count = db.Column(db.Integer, default=0)
    col_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default="uploaded")  # uploaded, profiled, cleaned, analyzed
    health_score = db.Column(db.Float, nullable=True)
    profile_json = db.Column(db.Text, nullable=True)
    cleaning_log = db.Column(db.Text, nullable=True)
    columns_metadata = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "row_count": self.row_count,
            "col_count": self.col_count,
            "status": self.status,
            "health_score": self.health_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
