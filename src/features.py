"""FairPay Feature Store Abstraction.

Provides a unified interface for feature engineering, storage, and retrieval
with support for multiple backends (SQLite, PostgreSQL, Redis, Feast).
"""
from __future__ import annotations

import json
import sqlite3
import warnings
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

FEATURE_DB = Path("data/features.db")


class FeatureStoreBackend(ABC):
    """Abstract base class for feature store backends."""
    
    @abstractmethod
    def write_features(self, entity_df: pd.DataFrame, features: pd.DataFrame, feature_names: list[str]):
        pass
    
    @abstractmethod
    def read_features(self, entity_df: pd.DataFrame, feature_names: list[str]) -> pd.DataFrame:
        pass
    
    @abstractmethod
    def get_feature_vector(self, entity_id: str, feature_names: list[str]) -> dict[str, Any]:
        pass
    
    @abstractmethod
    def list_features(self) -> list[str]:
        pass


class SQLiteFeatureStore(FeatureStoreBackend):
    """SQLite-based feature store for development and small-scale production."""
    
    def __init__(self, db_path: str | Path = FEATURE_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feature_definitions (
                    feature_name TEXT PRIMARY KEY,
                    feature_type TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feature_values (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    feature_name TEXT NOT NULL,
                    value TEXT NOT NULL,
                    event_timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_feature_values_entity 
                ON feature_values(entity_id, feature_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_feature_values_timestamp 
                ON feature_values(event_timestamp)
            """)
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def write_features(
        self,
        entity_df: pd.DataFrame,
        features: pd.DataFrame,
        feature_names: list[str],
    ):
        """Write feature values for entities."""
        if "entity_id" not in entity_df.columns:
            raise ValueError("entity_df must contain 'entity_id' column")
        
        with self._get_connection() as conn:
            now = datetime.now().isoformat()
            
            for feat in feature_names:
                if feat not in features.columns:
                    continue
                
                dtype = str(features[feat].dtype)
                conn.execute("""
                    INSERT OR REPLACE INTO feature_definitions 
                    (feature_name, feature_type, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (feat, dtype, f"Auto-registered feature {feat}", now, now))
            
            for _, row in entity_df.iterrows():
                entity_id = row["entity_id"]
                event_ts = row.get("event_timestamp", now)
                
                for feat in feature_names:
                    if feat in features.columns:
                        idx = entity_df.index.get_loc(_)
                        value = features.iloc[idx][feat]
                        if pd.notna(value):
                            conn.execute("""
                                INSERT INTO feature_values 
                                (entity_id, feature_name, value, event_timestamp)
                                VALUES (?, ?, ?, ?)
                            """, (entity_id, feat, json.dumps(value), event_ts))
    
    def read_features(self, entity_df: pd.DataFrame, feature_names: list[str]) -> pd.DataFrame:
        """Read latest feature values for entities."""
        if "entity_id" not in entity_df.columns:
            raise ValueError("entity_df must contain 'entity_id' column")
        
        entity_ids = entity_df["entity_id"].tolist()
        placeholders = ",".join(["?"] * len(entity_ids))
        
        with self._get_connection() as conn:
            query = f"""
                SELECT entity_id, feature_name, value, event_timestamp
                FROM feature_values
                WHERE entity_id IN ({placeholders})
                AND feature_name IN ({",".join(["?"] * len(feature_names))})
            """
            
            df = pd.read_sql_query(query, conn, params=entity_ids + feature_names)
        
        if df.empty:
            return pd.DataFrame(columns=["entity_id"] + feature_names)
        
        df["value"] = df["value"].apply(json.loads)
        
        pivot = df.pivot_table(
            index="entity_id",
            columns="feature_name",
            values="value",
            aggfunc="last",
        ).reset_index()
        
        result = entity_df[["entity_id"]].merge(pivot, on="entity_id", how="left")
        
        for feat in feature_names:
            if feat not in result.columns:
                result[feat] = np.nan
        
        return result[["entity_id"] + feature_names]
    
    def get_feature_vector(self, entity_id: str, feature_names: list[str]) -> dict[str, Any]:
        """Get latest feature vector for a single entity."""
        placeholders = ",".join(["?"] * len(feature_names))
        
        with self._get_connection() as conn:
            query = f"""
                SELECT feature_name, value
                FROM feature_values
                WHERE entity_id = ? AND feature_name IN ({placeholders})
                ORDER BY event_timestamp DESC
            """
            df = pd.read_sql_query(query, conn, params=[entity_id] + feature_names)
        
        if df.empty:
            return {feat: None for feat in feature_names}
        
        df["value"] = df["value"].apply(json.loads)
        latest = df.drop_duplicates(subset="feature_name", keep="first")
        
        return dict(zip(latest["feature_name"], latest["value"]))
    
    def list_features(self) -> list[str]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT feature_name FROM feature_definitions")
            return [row[0] for row in cursor.fetchall()]


class FeatureEngineer:
    """Feature engineering pipeline for salary prediction."""
    
    def __init__(self):
        self.fitted = False
        self.encoders = {}
        self.scalers = {}
        self.feature_names = []
    
    def fit(self, df: pd.DataFrame) -> "FeatureEngineer":
        """Fit feature engineering transforms on training data."""
        from sklearn.preprocessing import StandardScaler, LabelEncoder
        from sklearn.impute import SimpleImputer
        
        for col in NUMERICAL_FEATURES:
            if col in df.columns:
                imputer = SimpleImputer(strategy="median")
                scaler = StandardScaler()
                self.encoders[col] = imputer.fit(df[[col]])
                vals = imputer.transform(df[[col]])
                self.scalers[col] = scaler.fit(vals)
        
        for col in CATEGORICAL_FEATURES:
            if col in df.columns:
                le = LabelEncoder()
                self.encoders[col] = le.fit(df[col].astype(str))
        
        self.feature_names = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
        self.fitted = True
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply feature engineering transforms."""
        if not self.fitted:
            raise ValueError("FeatureEngineer must be fitted first")
        
        result = pd.DataFrame(index=df.index)
        
        for col in NUMERICAL_FEATURES:
            if col in df.columns:
                imputed = self.encoders[col].transform(df[[col]])
                scaled = self.scalers[col].transform(imputed)
                result[col] = scaled.flatten()
            else:
                result[col] = 0.0
        
        for col in CATEGORICAL_FEATURES:
            if col in df.columns:
                result[col] = self.encoders[col].transform(df[col].astype(str))
            else:
                result[col] = 0
        
        return result
    
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)


NUMERICAL_FEATURES = [
    "years_experience",
    "skills_count",
    "previous_salary",
    "interview_score",
]

CATEGORICAL_FEATURES = [
    "education_level",
    "job_role",
    "location",
    "company_size",
]

ALL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES


def create_feature_store(backend: str = "sqlite", **kwargs) -> FeatureStoreBackend:
    """Factory function to create feature store backend."""
    if backend == "sqlite":
        return SQLiteFeatureStore(**kwargs)
    elif backend == "postgresql":
        raise NotImplementedError("PostgreSQL backend not implemented yet")
    elif backend == "redis":
        raise NotImplementedError("Redis backend not implemented yet")
    elif backend == "feast":
        raise NotImplementedError("Feast backend not implemented yet")
    else:
        raise ValueError(f"Unknown backend: {backend}")


def materialize_features(
    source_df: pd.DataFrame,
    feature_store: FeatureStoreBackend,
    entity_id_col: str = "candidate_id",
    timestamp_col: str = "event_timestamp",
    batch_size: int = 1000,
):
    """Materialize features from source dataframe to feature store."""
    entity_df = source_df[[entity_id_col, timestamp_col]].rename(
        columns={entity_id_col: "entity_id", timestamp_col: "event_timestamp"}
    )
    feature_df = source_df[ALL_FEATURES].copy()
    
    for i in range(0, len(entity_df), batch_size):
        batch_entity = entity_df.iloc[i:i+batch_size]
        batch_features = feature_df.iloc[i:i+batch_size]
        feature_store.write_features(batch_entity, batch_features, ALL_FEATURES)
    
    print(f"Materialized {len(entity_df)} feature vectors")


def load_training_data(
    feature_store: FeatureStoreBackend,
    entity_ids: list[str],
    label_col: str = "salary",
) -> tuple[pd.DataFrame, pd.Series]:
    """Load training data from feature store."""
    entity_df = pd.DataFrame({"entity_id": entity_ids})
    features = feature_store.read_features(entity_df, ALL_FEATURES)
    
    labels_df = entity_df.copy()
    labels_df[label_col] = source_df[label_col] if "source_df" in globals() else np.nan
    
    return features, labels_df[label_col]


if __name__ == "__main__":
    store = SQLiteFeatureStore()
    print("Feature store initialized")
    print(f"Available features: {store.list_features()}")