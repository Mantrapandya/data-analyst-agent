"""File validation, parsing, and storage service."""

import os
import uuid
import pandas as pd

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def allowed_file(filename):
    """Check if file extension is supported."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def safe_filename(filename):
    """Generate a safe unique filename preserving extension."""
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else "csv"
    return f"{uuid.uuid4().hex}.{ext}"


def validate_upload(file_storage):
    """Validate an uploaded file. Returns (is_valid, error_message)."""
    if not file_storage or not file_storage.filename:
        return False, "No file selected."

    if not allowed_file(file_storage.filename):
        ext = file_storage.filename.rsplit(".", 1)[1] if "." in file_storage.filename else "unknown"
        return False, f"Unsupported file type: .{ext}. Supported: CSV, XLSX, XLS."

    # Check file size by reading content
    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)

    if size == 0:
        return False, "File is empty."

    if size > MAX_FILE_SIZE:
        mb = size / (1024 * 1024)
        return False, f"File too large ({mb:.1f} MB). Maximum is {MAX_FILE_SIZE // (1024*1024)} MB."

    return True, None


def parse_file(file_path):
    """Parse a CSV or Excel file into a DataFrame.

    Returns (df, error_message). On failure, df is None.
    """
    ext = file_path.rsplit(".", 1)[1].lower()

    try:
        if ext == "csv":
            # Try UTF-8 first, then latin-1 as fallback
            try:
                df = pd.read_csv(file_path, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding="latin-1")
        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(file_path, engine="openpyxl" if ext == "xlsx" else None)
        else:
            return None, f"Unsupported format: .{ext}"

        if df.empty:
            return None, "File contains no data rows."

        if len(df.columns) == 0:
            return None, "File contains no columns."

        # Check for duplicate column names
        dupes = df.columns[df.columns.duplicated()].tolist()
        if dupes:
            # Rename duplicates by appending suffix
            cols = []
            seen = {}
            for c in df.columns:
                if c in seen:
                    seen[c] += 1
                    cols.append(f"{c}_{seen[c]}")
                else:
                    seen[c] = 0
                    cols.append(c)
            df.columns = cols

        # Strip whitespace from column names
        df.columns = [str(c).strip() for c in df.columns]

        # Try to parse date columns
        for col in df.columns:
            if df[col].dtype == "object":
                sample = df[col].dropna().head(20)
                if len(sample) > 0:
                    try:
                        parsed = pd.to_datetime(sample, format="mixed", dayfirst=False)
                        if parsed.notna().sum() >= len(sample) * 0.8:
                            df[col] = pd.to_datetime(df[col], format="mixed", dayfirst=False, errors="coerce")
                    except (ValueError, TypeError):
                        pass

        return df, None

    except pd.errors.EmptyDataError:
        return None, "File is empty or contains no parseable data."
    except pd.errors.ParserError as e:
        return None, f"Failed to parse file: {str(e)[:200]}"
    except Exception as e:
        return None, f"Error reading file: {str(e)[:200]}"


def save_dataframe(df, directory, filename_prefix="cleaned"):
    """Save a DataFrame to CSV. Returns the file path."""
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{filename_prefix}_{uuid.uuid4().hex[:8]}.csv")
    df.to_csv(path, index=False)
    return path
