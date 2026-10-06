"""FairPay Model Monitoring & A/B Testing Module.

Implements model performance monitoring, A/B testing framework,
and automated alerting for production ML systems.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import warnings
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

MONITOR_DB = Path("data/monitor.db")


def get_monitor_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(MONITOR_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def monitor_transaction():
    conn = get_monitor_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_monitor_db():
    MONITOR_DB.parent.mkdir(parents=True, exist_ok=True)
    
    with monitor_transaction() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model_version TEXT NOT NULL,
                model_variant TEXT NOT NULL,
                mae REAL,
                rmse REAL,
                r2 REAL,
                sample_count INTEGER,
                latency_p50 REAL,
                latency_p95 REAL,
                latency_p99 REAL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ab_test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                experiment_name TEXT NOT NULL,
                variant TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                sample_size INTEGER,
                p_value REAL,
                significant BOOLEAN
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                model_version TEXT,
                metric_name TEXT,
                metric_value REAL,
                threshold_value REAL,
                acknowledged BOOLEAN DEFAULT FALSE
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feature_drift_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                feature_name TEXT NOT NULL,
                drift_score REAL,
                drift_type TEXT,
                threshold REAL,
                detected BOOLEAN
            )
        """)
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON model_performance(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ab_timestamp ON ab_test_results(timestamp)")


class ModelMonitor:
    """Production model monitoring with alerting."""
    
    def __init__(
        self,
        model_version: str,
        mae_threshold: float = 20000,
        rmse_threshold: float = 30000,
        latency_p95_threshold: float = 1.0,
        drift_threshold: float = 0.1,
    ):
        self.model_version = model_version
        self.mae_threshold = mae_threshold
        self.rmse_threshold = rmse_threshold
        self.latency_p95_threshold = latency_p95_threshold
        self.drift_threshold = drift_threshold
        self._latencies = []
        self._predictions = []
        self._lock = threading.Lock()
        
        init_monitor_db()
    
    def record_prediction(
        self,
        y_true: float | None,
        y_pred: float,
        latency: float,
        variant: str = "A",
    ):
        with self._lock:
            self._latencies.append(latency)
            self._predictions.append((y_true, y_pred))
    
    def check_and_alert(self) -> list[dict]:
        alerts = []
        
        with self._lock:
            if len(self._latencies) >= 100:
                latencies = np.array(self._latencies[-1000:])
                p95 = np.percentile(latencies, 95)
                
                if p95 > self.latency_p95_threshold:
                    alerts.append({
                        "type": "latency",
                        "severity": "warning",
                        "message": f"P95 latency ({p95:.3f}s) exceeds threshold ({self.latency_p95_threshold}s)",
                        "metric_value": p95,
                        "threshold": self.latency_p95_threshold,
                    })
            
            if len(self._predictions) >= 50:
                recent = self._predictions[-200:]
                y_true_vals = [p[0] for p in recent if p[0] is not None]
                y_pred_vals = [p[1] for p in recent if p[0] is not None]
                
                if len(y_true_vals) >= 30:
                    mae = np.mean(np.abs(np.array(y_true_vals) - np.array(y_pred_vals)))
                    rmse = np.sqrt(np.mean((np.array(y_true_vals) - np.array(y_pred_vals)) ** 2))
                    
                    if mae > self.mae_threshold:
                        alerts.append({
                            "type": "performance",
                            "severity": "critical",
                            "message": f"MAE ({mae:,.0f}) exceeds threshold ({self.mae_threshold:,.0f})",
                            "metric_value": mae,
                            "threshold": self.mae_threshold,
                        })
                    
                    if rmse > self.rmse_threshold:
                        alerts.append({
                            "type": "performance",
                            "severity": "warning",
                            "message": f"RMSE ({rmse:,.0f}) exceeds threshold ({self.rmse_threshold:,.0f})",
                            "metric_value": rmse,
                            "threshold": self.rmse_threshold,
                        })
        
        for alert in alerts:
            self._save_alert(alert)
        
        return alerts
    
    def _save_alert(self, alert: dict):
        with monitor_transaction() as conn:
            conn.execute("""
                INSERT INTO alerts (timestamp, alert_type, severity, message, model_version, metric_name, metric_value, threshold_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                alert["type"],
                alert["severity"],
                alert["message"],
                self.model_version,
                alert.get("metric_name", ""),
                alert.get("metric_value"),
                alert.get("threshold"),
            ))
    
    def flush_metrics(self, variant: str = "A"):
        with self._lock:
            if not self._latencies:
                return
            
            latencies = np.array(self._latencies)
            self._latencies = []
            
            predictions = self._predictions
            self._predictions = []
        
        if not predictions:
            return
        
        y_true_vals = [p[0] for p in predictions if p[0] is not None]
        y_pred_vals = [p[1] for p in predictions if p[0] is not None]
        
        if len(y_true_vals) >= 10:
            mae = np.mean(np.abs(np.array(y_true_vals) - np.array(y_pred_vals)))
            rmse = np.sqrt(np.mean((np.array(y_true_vals) - np.array(y_pred_vals)) ** 2))
            r2 = 1 - np.sum((np.array(y_true_vals) - np.array(y_pred_vals)) ** 2) / np.sum((np.array(y_true_vals) - np.mean(y_true_vals)) ** 2)
        else:
            mae = rmse = r2 = None
        
        with monitor_transaction() as conn:
            conn.execute("""
                INSERT INTO model_performance (timestamp, model_version, model_variant, mae, rmse, r2, sample_count, latency_p50, latency_p95, latency_p99)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                self.model_version,
                variant,
                mae,
                rmse,
                r2,
                len(predictions),
                np.percentile(latencies, 50) if len(latencies) > 0 else None,
                np.percentile(latencies, 95) if len(latencies) > 0 else None,
                np.percentile(latencies, 99) if len(latencies) > 0 else None,
            ))


class ABTestFramework:
    """A/B testing framework for model variants."""
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.variants = {}
        init_monitor_db()
    
    def register_variant(self, variant_name: str, allocation: float = 0.5):
        """Register a model variant with traffic allocation."""
        self.variants[variant_name] = {
            "allocation": allocation,
            "predictions": [],
            "latencies": [],
            "ground_truth": [],
        }
    
    def assign_variant(self, user_id: str | int) -> str:
        """Deterministically assign user to variant."""
        if not self.variants:
            return "A"
        
        hash_val = hash(f"{self.experiment_name}:{user_id}")
        bucket = (hash_val % 10000) / 10000
        
        cumulative = 0
        for variant_name, config in self.variants.items():
            cumulative += config["allocation"]
            if bucket < cumulative:
                return variant_name
        
        return list(self.variants.keys())[-1]
    
    def record_result(
        self,
        variant: str,
        y_true: float | None,
        y_pred: float,
        latency: float,
    ):
        if variant in self.variants:
            if y_true is not None:
                self.variants[variant]["ground_truth"].append((y_true, y_pred))
            self.variants[variant]["latencies"].append(latency)
    
    def analyze(self, metric: str = "mae", min_samples: int = 30) -> dict[str, Any]:
        """Run statistical analysis on experiment results."""
        results = {}
        
        for variant_name, data in self.variants.items():
            gt = data["ground_truth"]
            if len(gt) >= min_samples:
                y_true = np.array([g[0] for g in gt])
                y_pred = np.array([g[1] for g in gt])
                
                if metric == "mae":
                    value = np.mean(np.abs(y_true - y_pred))
                elif metric == "rmse":
                    value = np.sqrt(np.mean((y_true - y_pred) ** 2))
                elif metric == "r2":
                    value = 1 - np.sum((y_true - y_pred) ** 2) / np.sum((y_true - np.mean(y_true)) ** 2)
                else:
                    value = None
                
                results[variant_name] = {
                    "metric": metric,
                    "value": value,
                    "sample_size": len(gt),
                    "latency_p50": np.percentile(data["latencies"], 50) if data["latencies"] else None,
                    "latency_p95": np.percentile(data["latencies"], 95) if data["latencies"] else None,
                }
        
        if len(results) >= 2:
            variant_names = list(results.keys())
            v1, v2 = variant_names[0], variant_names[1]
            
            gt1 = np.array([g[1] for g in self.variants[v1]["ground_truth"]])
            gt2 = np.array([g[1] for g in self.variants[v2]["ground_truth"]])
            
            if len(gt1) >= min_samples and len(gt2) >= min_samples:
                t_stat, p_value = stats.ttest_ind(gt1, gt2)
                significant = p_value < 0.05
                
                results["comparison"] = {
                    "variant_a": v1,
                    "variant_b": v2,
                    "t_statistic": float(t_stat),
                    "p_value": float(p_value),
                    "significant": significant,
                    "winner": v1 if results[v1]["value"] < results[v2]["value"] else v2,
                }
                
                with monitor_transaction() as conn:
                    conn.execute("""
                        INSERT INTO ab_test_results (timestamp, experiment_name, variant, metric_name, metric_value, sample_size, p_value, significant)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        datetime.now().isoformat(),
                        self.experiment_name,
                        f"{v1}_vs_{v2}",
                        metric,
                        results["comparison"]["winner"] == v1 and results[v1]["value"] or results[v2]["value"],
                        min(len(gt1), len(gt2)),
                        p_value,
                        significant,
                    ))
        
        return results
    
    def get_results(self) -> dict[str, Any]:
        return {k: {
            "allocation": v["allocation"],
            "samples": len(v["ground_truth"]),
            "latency_avg": np.mean(v["latencies"]) if v["latencies"] else None,
        } for k, v in self.variants.items()}


def get_alerts(
    hours: int = 24,
    severity: str | None = None,
    acknowledged: bool | None = None,
) -> pd.DataFrame:
    with get_monitor_connection() as conn:
        query = "SELECT * FROM alerts WHERE timestamp >= ?"
        params = [(datetime.now() - timedelta(hours=hours)).isoformat()]
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        if acknowledged is not None:
            query += " AND acknowledged = ?"
            params.append(acknowledged)
        
        query += " ORDER BY timestamp DESC"
        return pd.read_sql_query(query, conn, params=params)


def acknowledge_alert(alert_id: int):
    with monitor_transaction() as conn:
        conn.execute("UPDATE alerts SET acknowledged = TRUE WHERE id = ?", (alert_id,))


def get_performance_history(
    model_version: str | None = None,
    hours: int = 168,
) -> pd.DataFrame:
    with get_monitor_connection() as conn:
        query = "SELECT * FROM model_performance WHERE timestamp >= ?"
        params = [(datetime.now() - timedelta(hours=hours)).isoformat()]
        
        if model_version:
            query += " AND model_version = ?"
            params.append(model_version)
        
        query += " ORDER BY timestamp DESC"
        return pd.read_sql_query(query, conn, params=params)


def get_ab_test_history(experiment_name: str | None = None) -> pd.DataFrame:
    with get_monitor_connection() as conn:
        query = "SELECT * FROM ab_test_results"
        params = []
        
        if experiment_name:
            query += " WHERE experiment_name = ?"
            params.append(experiment_name)
        
        query += " ORDER BY timestamp DESC"
        return pd.read_sql_query(query, conn, params=params)


if __name__ == "__main__":
    init_monitor_db()
    print("Monitor database initialized")