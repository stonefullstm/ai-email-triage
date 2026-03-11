import sqlite3
import numpy as np
from pathlib import Path
from triage.core.base import EmailInput


DB_PATH = Path(__file__).parent.parent / "database" / "triagedb.db"


class ExampleStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vector_embeddings (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT,
                    sender  TEXT,
                    label   TEXT NOT NULL,
                    vector  BLOB NOT NULL
                )
            """)

    def add(self, email: EmailInput, label: str, vector: np.ndarray) -> None:
        blob = vector.astype(np.float32).tobytes()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO vector_embeddings
                (subject, sender, label, vector) VALUES (?, ?, ?, ?)""",
                (email.subject, email.sender, label, blob),
            )

    def load_all(self, dims: int = 384) -> list[tuple[np.ndarray, str]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
               "SELECT vector, label FROM vector_embeddings").fetchall()
        return [
            (np.frombuffer(row[0], dtype=np.float32), row[1])
            for row in rows
        ]

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(
               "SELECT COUNT(*) FROM vector_embeddings").fetchone()[0]
