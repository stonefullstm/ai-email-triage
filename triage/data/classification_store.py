import sqlite3
from pathlib import Path
from datetime import datetime


DB_PATH = Path(__file__).parent.parent / "database" / "triagedb.db"


class ClassificationStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS classifications (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    label      TEXT NOT NULL,
                    source     TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    subject    TEXT,
                    sender     TEXT,
                    classified_at TEXT NOT NULL
                )
            """)

    def add(
            self,
            label: str,
            source: str,
            confidence: float,
            subject: str = "",
            sender: str = ""
          ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO classifications
                   (label, source, confidence, subject, sender, classified_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (label, source, round(confidence, 4), subject, sender,
                 datetime.now().isoformat()),
            )

    def summary(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            by_label = conn.execute("""
                SELECT label, COUNT(*) as total
                FROM classifications
                GROUP BY label ORDER BY total DESC
            """).fetchall()

            by_source = conn.execute("""
                SELECT source, COUNT(*) as total,
                       ROUND(AVG(confidence), 3) as avg_confidence
                FROM classifications
                GROUP BY source ORDER BY total DESC
            """).fetchall()

            total = conn.execute(
                "SELECT COUNT(*) FROM classifications").fetchone()[0]

        return {
            "total": total,
            "by_label": by_label,
            "by_source": by_source,
        }
