"""FairPay Database Module - SQLite backend for persistence."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

DB_PATH = Path("data/fairpay.db")


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_transaction() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database transactions."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database() -> None:
    """Initialize database schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with db_transaction() as conn:
        # Predictions history
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                input_data TEXT NOT NULL,
                predicted_salary REAL NOT NULL,
                lower_bound REAL NOT NULL,
                upper_bound REAL NOT NULL,
                model_version TEXT NOT NULL,
                user_id TEXT,
                notes TEXT
            )
        """)

        # Batch predictions
        conn.execute("""
            CREATE TABLE IF NOT EXISTS batch_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                filename TEXT NOT NULL,
                num_candidates INTEGER NOT NULL,
                mean_predicted REAL NOT NULL,
                status TEXT NOT NULL,
                results_path TEXT
            )
        """)

        # Model metrics tracking
        conn.execute("""
            CREATE TABLE IF NOT EXISTS model_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model_version TEXT NOT NULL,
                mae REAL,
                rmse REAL,
                r2 REAL,
                fairness_gender_gap REAL,
                fairness_age_gap REAL,
                data_drift_score REAL
            )
        """)

        # Audit log
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                user_id TEXT,
                details TEXT,
                ip_address TEXT
            )
        """)

        # Settings
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_batch_timestamp ON batch_predictions(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")


def log_prediction(
    input_data: dict,
    predicted_salary: float,
    lower_bound: float,
    upper_bound: float,
    model_version: str = "1.0",
    user_id: str | None = None,
    notes: str | None = None,
) -> int:
    """Log a prediction to database."""
    with db_transaction() as conn:
        cursor = conn.execute(
            """
            INSERT INTO predictions (timestamp, input_data, predicted_salary, lower_bound, upper_bound, model_version, user_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                datetime.now().isoformat(),
                json.dumps(input_data),
                predicted_salary,
                lower_bound,
                upper_bound,
                model_version,
                user_id,
                notes,
            ),
        )
        return int(cursor.lastrowid or 0)


def log_batch_prediction(
    filename: str, num_candidates: int, mean_predicted: float, status: str, results_path: str | None = None
) -> int:
    """Log a batch prediction."""
    with db_transaction() as conn:
        cursor = conn.execute(
            """
            INSERT INTO batch_predictions (timestamp, filename, num_candidates, mean_predicted, status, results_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (datetime.now().isoformat(), filename, num_candidates, mean_predicted, status, results_path),
        )
        return int(cursor.lastrowid or 0)


def log_model_metrics(
    model_version: str,
    mae: float | None = None,
    rmse: float | None = None,
    r2: float | None = None,
    fairness_gender_gap: float | None = None,
    fairness_age_gap: float | None = None,
    data_drift_score: float | None = None,
) -> int:
    """Log model performance metrics."""
    with db_transaction() as conn:
        cursor = conn.execute(
            """
            INSERT INTO model_metrics (timestamp, model_version, mae, rmse, r2, fairness_gender_gap, fairness_age_gap, data_drift_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                datetime.now().isoformat(),
                model_version,
                mae,
                rmse,
                r2,
                fairness_gender_gap,
                fairness_age_gap,
                data_drift_score,
            ),
        )
        return int(cursor.lastrowid or 0)


def log_audit(
    action: str, user_id: str | None = None, details: dict | None = None, ip_address: str | None = None
) -> int:
    """Log an audit event."""
    with db_transaction() as conn:
        cursor = conn.execute(
            """
            INSERT INTO audit_log (timestamp, action, user_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?)
        """,
            (datetime.now().isoformat(), action, user_id, json.dumps(details) if details else None, ip_address),
        )
        return int(cursor.lastrowid or 0)


def get_prediction_history(limit: int = 100) -> pd.DataFrame:
    """Get prediction history."""
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT * FROM predictions ORDER BY timestamp DESC LIMIT ?
        """,
            conn,
            params=(limit,),
        )


def get_batch_history(limit: int = 50) -> pd.DataFrame:
    """Get batch prediction history."""
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT * FROM batch_predictions ORDER BY timestamp DESC LIMIT ?
        """,
            conn,
            params=(limit,),
        )


def get_model_metrics_history(limit: int = 50) -> pd.DataFrame:
    """Get model metrics history."""
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT * FROM model_metrics ORDER BY timestamp DESC LIMIT ?
        """,
            conn,
            params=(limit,),
        )


def get_audit_log(limit: int = 200) -> pd.DataFrame:
    """Get audit log."""
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?
        """,
            conn,
            params=(limit,),
        )


def get_setting(key: str, default: str | None = None) -> str | None:
    """Get a setting value."""
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    """Set a setting value."""
    with db_transaction() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
        """,
            (key, value, datetime.now().isoformat()),
        )


def get_prediction_stats() -> dict[str, Any]:
    """Get aggregate prediction statistics."""
    with get_connection() as conn:
        stats = {}
        stats["total_predictions"] = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
        stats["avg_salary"] = conn.execute("SELECT AVG(predicted_salary) FROM predictions").fetchone()[0] or 0
        stats["min_salary"] = conn.execute("SELECT MIN(predicted_salary) FROM predictions").fetchone()[0] or 0
        stats["max_salary"] = conn.execute("SELECT MAX(predicted_salary) FROM predictions").fetchone()[0] or 0

        # By role
        role_stats = pd.read_sql_query(
            """
            SELECT
                json_extract(input_data, '$.job_role') as role,
                COUNT(*) as count,
                AVG(predicted_salary) as avg_salary
            FROM predictions
            GROUP BY role
            ORDER BY avg_salary DESC
        """,
            conn,
        )
        stats["by_role"] = role_stats.to_dict("records")

        # By location
        loc_stats = pd.read_sql_query(
            """
            SELECT
                json_extract(input_data, '$.location') as location,
                COUNT(*) as count,
                AVG(predicted_salary) as avg_salary
            FROM predictions
            GROUP BY location
            ORDER BY avg_salary DESC
        """,
            conn,
        )
        stats["by_location"] = loc_stats.to_dict("records")

        return stats


# Initialize on import
init_database()
