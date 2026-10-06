"""FairSalary AI - Data Loader"""
import pandas as pd
from pathlib import Path
from typing import Optional


def load_raw_data(data_path: Optional[str] = None) -> pd.DataFrame:
    """Load raw salary data from CSV.

    Args:
        data_path: Path to CSV file. If None, uses default location.

    Returns:
        Loaded DataFrame with raw salary data.
    """
    if data_path is None:
        project_root = Path(__file__).parent.parent.parent.parent
        data_path = project_root / "ml" / "data" / "raw" / "salary_data.csv"

    return pd.read_csv(data_path)


def load_processed_data(data_path: Optional[str] = None) -> pd.DataFrame:
    """Load processed salary data from parquet.

    Args:
        data_path: Path to parquet file. If None, uses default location.

    Returns:
        Loaded DataFrame with processed salary data.
    """
    if data_path is None:
        project_root = Path(__file__).parent.parent.parent.parent
        data_path = project_root / "ml" / "data" / "processed" / "salary_data.parquet"

    return pd.read_parquet(data_path)


def save_processed_data(df: pd.DataFrame, data_path: Optional[str] = None) -> None:
    """Save processed data to parquet.

    Args:
        df: DataFrame to save.
        data_path: Path to save parquet file. If None, uses default location.
    """
    if data_path is None:
        project_root = Path(__file__).parent.parent.parent.parent
        data_path = project_root / "ml" / "data" / "processed" / "salary_data.parquet"

    data_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(data_path, index=False)


def get_data_info(df: pd.DataFrame) -> dict:
    """Get basic information about the dataset.

    Args:
        df: Input DataFrame.

    Returns:
        Dictionary with dataset information.
    """
    return {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
    }