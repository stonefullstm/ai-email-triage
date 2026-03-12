import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "triagedb.db"


class ProcessedStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed (
                    message_id   TEXT PRIMARY KEY,
                    label        TEXT,
                    source       TEXT,
                    processed_at TEXT NOT NULL
                )
            """)

    def is_processed(self, message_id: str) -> bool:
        if not message_id:
            return False
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM processed WHERE message_id = ?",
                (message_id,)
            ).fetchone()
        return row is not None

    def mark(self, message_id: str, label: str = "", source: str = "") -> None:
        if not message_id:
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR IGNORE INTO processed
                   (message_id, label, source, processed_at)
                   VALUES (?, ?, ?, ?)""",
                (message_id, label, source, datetime.now().isoformat()),
            )

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM processed").fetchone()[0]
