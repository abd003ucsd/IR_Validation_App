"""
Audit trail for IR Data Validation Tool.

Stores run history in a local SQLite database so analysts can
review past validations, compare scores over time, and download
previous results.

Schema
------
validation_runs
    id, timestamp, approach, source_a_name, source_b_name,
    key_cols_a, key_cols_b, score, total_keys, joined_count,
    missing_in_a, missing_in_b, mismatch_count,
    column_pairs, composite_pairs, results_csv
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Optional


_DB_PATH = None


def _get_db_path() -> str:
    global _DB_PATH
    if _DB_PATH is None:
        # Store the DB next to the app files
        _DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".audit", "validation_runs.db")
        os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    return _DB_PATH


def _get_conn() -> sqlite3.Connection:
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the audit database and table if they don't exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS validation_runs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            approach    TEXT NOT NULL,
            source_a_name TEXT,
            source_b_name TEXT,
            key_cols_a  TEXT,
            key_cols_b  TEXT,
            score       REAL,
            total_keys  INTEGER,
            joined_count INTEGER,
            missing_in_a INTEGER DEFAULT 0,
            missing_in_b INTEGER DEFAULT 0,
            mismatch_count INTEGER DEFAULT 0,
            column_pairs  TEXT,
            composite_pairs TEXT,
            results_csv TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_run(
    approach: str,
    score: float,
    total_keys: int,
    joined_count: int,
    missing_in_a: int = 0,
    missing_in_b: int = 0,
    mismatch_count: int = 0,
    source_a_name: Optional[str] = None,
    source_b_name: Optional[str] = None,
    key_cols_a: Optional[list] = None,
    key_cols_b: Optional[list] = None,
    column_pairs: Optional[list] = None,
    composite_pairs: Optional[list] = None,
    results_csv: Optional[str] = None,
) -> int:
    """Record a validation run and return its ID."""
    conn = _get_conn()
    now = datetime.now().isoformat()
    cursor = conn.execute(
        """INSERT INTO validation_runs
           (timestamp, approach, source_a_name, source_b_name,
            key_cols_a, key_cols_b, score, total_keys, joined_count,
            missing_in_a, missing_in_b, mismatch_count,
            column_pairs, composite_pairs, results_csv)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            now, approach, source_a_name, source_b_name,
            json.dumps(key_cols_a or []), json.dumps(key_cols_b or []),
            score, total_keys, joined_count,
            missing_in_a, missing_in_b, mismatch_count,
            json.dumps(column_pairs or []), json.dumps(composite_pairs or []),
            results_csv,
        ),
    )
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id


def get_recent_runs(limit: int = 20) -> list[dict]:
    """Return the most recent validation runs."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM validation_runs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_run(run_id: int) -> Optional[dict]:
    """Return a single run by ID."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM validation_runs WHERE id = ?", (run_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_old_runs(keep: int = 100):
    """Delete runs beyond the keep threshold to limit DB size."""
    conn = _get_conn()
    conn.execute(
        """DELETE FROM validation_runs WHERE id NOT IN
           (SELECT id FROM validation_runs ORDER BY id DESC LIMIT ?)""",
        (keep,),
    )
    conn.commit()
    conn.close()
