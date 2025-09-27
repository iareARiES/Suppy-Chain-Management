"""
Input/Output utilities for data persistence.
"""
import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_dir(path: str) -> None:
    """Ensure directory exists."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def write_json(data: Any, filepath: str, indent: int = 2) -> None:
    """
    Write data to JSON file.
    
    Args:
        data: Data to write
        filepath: Output file path
        indent: JSON indentation
    """
    ensure_dir(filepath)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, default=str, ensure_ascii=False)
        logger.info(f"Wrote JSON data to {filepath}")
    except Exception as e:
        logger.error(f"Failed to write JSON to {filepath}: {e}")
        raise


def read_json(filepath: str) -> Any:
    """
    Read data from JSON file.
    
    Args:
        filepath: Input file path
        
    Returns:
        Parsed JSON data
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read JSON from {filepath}: {e}")
        raise


def write_parquet(df: pd.DataFrame, filepath: str) -> None:
    """
    Write DataFrame to Parquet file.
    
    Args:
        df: DataFrame to write
        filepath: Output file path
    """
    ensure_dir(filepath)
    try:
        df.to_parquet(filepath, index=False, engine='pyarrow')
        logger.info(f"Wrote {len(df)} rows to Parquet file {filepath}")
    except Exception as e:
        logger.error(f"Failed to write Parquet to {filepath}: {e}")
        raise


def read_parquet(filepath: str) -> pd.DataFrame:
    """
    Read DataFrame from Parquet file.
    
    Args:
        filepath: Input file path
        
    Returns:
        DataFrame
    """
    try:
        df = pd.read_parquet(filepath, engine='pyarrow')
        logger.info(f"Read {len(df)} rows from Parquet file {filepath}")
        return df
    except Exception as e:
        logger.error(f"Failed to read Parquet from {filepath}: {e}")
        raise


def write_csv(df: pd.DataFrame, filepath: str, index: bool = False) -> None:
    """
    Write DataFrame to CSV file.
    
    Args:
        df: DataFrame to write
        filepath: Output file path
        index: Whether to include index
    """
    ensure_dir(filepath)
    try:
        df.to_csv(filepath, index=index, encoding='utf-8')
        logger.info(f"Wrote {len(df)} rows to CSV file {filepath}")
    except Exception as e:
        logger.error(f"Failed to write CSV to {filepath}: {e}")
        raise


def read_csv(filepath: str, **kwargs) -> pd.DataFrame:
    """
    Read DataFrame from CSV file.
    
    Args:
        filepath: Input file path
        **kwargs: Additional arguments for pd.read_csv
        
    Returns:
        DataFrame
    """
    try:
        df = pd.read_csv(filepath, encoding='utf-8', **kwargs)
        logger.info(f"Read {len(df)} rows from CSV file {filepath}")
        return df
    except Exception as e:
        logger.error(f"Failed to read CSV from {filepath}: {e}")
        raise


def write_yaml(data: Any, filepath: str) -> None:
    """
    Write data to YAML file.
    
    Args:
        data: Data to write
        filepath: Output file path
    """
    try:
        import yaml
        ensure_dir(filepath)
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        logger.info(f"Wrote YAML data to {filepath}")
    except ImportError:
        logger.error("PyYAML not available, cannot write YAML files")
        raise
    except Exception as e:
        logger.error(f"Failed to write YAML to {filepath}: {e}")
        raise


def read_yaml(filepath: str) -> Any:
    """
    Read data from YAML file.
    
    Args:
        filepath: Input file path
        
    Returns:
        Parsed YAML data
    """
    try:
        import yaml
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.error("PyYAML not available, cannot read YAML files")
        raise
    except Exception as e:
        logger.error(f"Failed to read YAML from {filepath}: {e}")
        raise


def append_parquet(df: pd.DataFrame, filepath: str) -> None:
    """
    Append DataFrame to existing Parquet file or create new one.
    
    Args:
        df: DataFrame to append
        filepath: Parquet file path
    """
    if os.path.exists(filepath):
        try:
            existing_df = read_parquet(filepath)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            write_parquet(combined_df, filepath)
        except Exception as e:
            logger.warning(f"Failed to append to existing Parquet file, creating new: {e}")
            write_parquet(df, filepath)
    else:
        write_parquet(df, filepath)


def safe_read_parquet(filepath: str, default: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Safely read Parquet file, returning default if file doesn't exist.
    
    Args:
        filepath: Parquet file path
        default: Default DataFrame to return if file doesn't exist
        
    Returns:
        DataFrame
    """
    if os.path.exists(filepath):
        return read_parquet(filepath)
    else:
        if default is not None:
            return default
        else:
            return pd.DataFrame()


def safe_read_csv(filepath: str, default: Optional[pd.DataFrame] = None, **kwargs) -> pd.DataFrame:
    """
    Safely read CSV file, returning default if file doesn't exist.
    
    Args:
        filepath: CSV file path
        default: Default DataFrame to return if file doesn't exist
        **kwargs: Additional arguments for pd.read_csv
        
    Returns:
        DataFrame
    """
    if os.path.exists(filepath):
        return read_csv(filepath, **kwargs)
    else:
        if default is not None:
            return default
        else:
            return pd.DataFrame()


def get_file_size(filepath: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        filepath: File path
        
    Returns:
        File size in bytes
    """
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0


def list_files(directory: str, pattern: str = "*") -> List[str]:
    """
    List files in directory matching pattern.
    
    Args:
        directory: Directory path
        pattern: File pattern (e.g., "*.csv", "*.parquet")
        
    Returns:
        List of file paths
    """
    try:
        return [str(f) for f in Path(directory).glob(pattern)]
    except Exception as e:
        logger.error(f"Failed to list files in {directory}: {e}")
        return []


def backup_file(filepath: str, backup_suffix: str = ".backup") -> str:
    """
    Create backup of file.
    
    Args:
        filepath: File to backup
        backup_suffix: Suffix for backup file
        
    Returns:
        Backup file path
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    backup_path = f"{filepath}{backup_suffix}"
    ensure_dir(backup_path)
    
    import shutil
    shutil.copy2(filepath, backup_path)
    logger.info(f"Created backup: {backup_path}")
    return backup_path


def clean_old_files(directory: str, pattern: str, max_age_days: int = 7) -> int:
    """
    Clean old files from directory.
    
    Args:
        directory: Directory to clean
        pattern: File pattern to match
        max_age_days: Maximum age in days
        
    Returns:
        Number of files deleted
    """
    import time
    from datetime import datetime, timedelta
    
    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
    deleted_count = 0
    
    try:
        for filepath in Path(directory).glob(pattern):
            if filepath.stat().st_mtime < cutoff_time:
                filepath.unlink()
                deleted_count += 1
                logger.info(f"Deleted old file: {filepath}")
    except Exception as e:
        logger.error(f"Failed to clean old files in {directory}: {e}")
    
    return deleted_count


def write_text(text: str, file_path: str) -> None:
    """Write text to file."""
    ensure_dir(file_path)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        logger.info(f"Wrote text to {file_path}")
    except Exception as e:
        logger.error(f"Failed to write text to {file_path}: {e}")
        raise