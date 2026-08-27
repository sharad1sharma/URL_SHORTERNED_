import sqlite3
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "urls.db"
CSV_PATH = BASE_DIR / "database" / "urls.csv"

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT NOT NULL,
                short_code TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                click_count INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()

def export_to_csv():
    """Export all URL rows to urls.csv so it can be viewed/edited in MS Excel."""
    try:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM urls ORDER BY id").fetchall()

        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Header row
            writer.writerow(["id", "original_url", "short_code", "created_at", "updated_at", "click_count"])
            for row in rows:
                writer.writerow([
                    row["id"],
                    row["original_url"],
                    row["short_code"],
                    row["created_at"],
                    row["updated_at"],
                    row["click_count"],
                ])
    except Exception as e:
        print(f"[CSV export] Warning: could not write {CSV_PATH}: {e}")

