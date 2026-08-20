"""
Schema Inference and Table Name Generation Service
Infers conservative PostgreSQL data types, profiles column distributions,
and generates safe PostgreSQL table and column identifiers.
"""

import re
from typing import List, Dict, Tuple, Optional
import pandas as pd
import database
from backend.schemas.dataset import ColumnProfile


def is_boolean_series(series: pd.Series) -> bool:
    """Checks if a series contains exclusively boolean representations."""
    if pd.api.types.is_bool_dtype(series):
        return True
    non_null = series.dropna().astype(str).str.strip().str.lower()
    if len(non_null) == 0:
        return False
    bool_values = {'true', 'false', 't', 'f', '1', '0', 'yes', 'no'}
    unique_vals = set(non_null.unique())
    return unique_vals.issubset(bool_values) and len(unique_vals) <= 2


def is_integer_series(series: pd.Series) -> Tuple[bool, str]:
    """
    Checks if a series contains integer values.
    Returns (is_integer, 'INTEGER' or 'BIGINT').
    """
    if pd.api.types.is_integer_dtype(series):
        non_null = series.dropna()
        if len(non_null) == 0:
            return True, "INTEGER"
        min_v, max_v = non_null.min(), non_null.max()
        if -2147483648 <= min_v and max_v <= 2147483647:
            return True, "INTEGER"
        return True, "BIGINT"

    # Try numeric conversion
    non_null = series.dropna()
    if len(non_null) == 0:
        return False, "TEXT"

    try:
        # Check if all non-null values can be converted to float/int without fractional parts
        converted = pd.to_numeric(non_null, errors='raise')
        # Check if identical to integer cast
        if (converted % 1 == 0).all():
            min_v, max_v = converted.min(), converted.max()
            if -2147483648 <= min_v and max_v <= 2147483647:
                return True, "INTEGER"
            return True, "BIGINT"
        return False, "TEXT"
    except (ValueError, TypeError, OverflowError):
        return False, "TEXT"


def is_numeric_series(series: pd.Series) -> bool:
    """Checks if a series contains floating-point decimal numbers."""
    if pd.api.types.is_float_dtype(series):
        return True
    non_null = series.dropna()
    if len(non_null) == 0:
        return False
    try:
        pd.to_numeric(non_null, errors='raise')
        return True
    except (ValueError, TypeError):
        return False


def is_date_or_timestamp_series(series: pd.Series) -> Tuple[bool, str]:
    """
    Checks if a series contains standard Date or Timestamp values.
    Returns (is_date_or_ts, 'DATE' or 'TIMESTAMP').
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        # Check if time component is zero for all rows
        non_null = series.dropna()
        if len(non_null) == 0:
            return True, "DATE"
        if (non_null.dt.hour == 0).all() and (non_null.dt.minute == 0).all() and (non_null.dt.second == 0).all():
            return True, "DATE"
        return True, "TIMESTAMP"

    non_null = series.dropna().astype(str).str.strip()
    if len(non_null) == 0:
        return False, "TEXT"

    # Quick regex heuristic to avoid slow date parsing on arbitrary strings
    date_pattern = r'^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}'
    sample = non_null.iloc[:50]
    matches_pattern = sample.str.match(date_pattern).all()
    if not matches_pattern:
        return False, "TEXT"

    try:
        parsed = pd.to_datetime(sample, errors='raise', format='mixed')
        has_time = (parsed.dt.hour != 0).any() or (parsed.dt.minute != 0).any()
        return True, "TIMESTAMP" if has_time else "DATE"
    except Exception:
        return False, "TEXT"


def infer_postgresql_type(series: pd.Series) -> str:
    """
    Conservatively infers the best PostgreSQL data type for a Pandas Series.
    Falls back safely to TEXT if values are ambiguous.
    """
    non_null = series.dropna()
    if len(non_null) == 0:
        return "TEXT"

    # 1. Check Boolean
    if is_boolean_series(series):
        return "BOOLEAN"

    # 2. Check Integer / BigInt
    is_int, int_type = is_integer_series(series)
    if is_int:
        return int_type

    # 3. Check Numeric / Float
    if is_numeric_series(series):
        return "NUMERIC"

    # 4. Check Date / Timestamp
    is_dt, dt_type = is_date_or_timestamp_series(series)
    if is_dt:
        return dt_type

    # 5. Safe Fallback
    return "TEXT"


def generate_safe_table_name(raw_name: str, existing_tables: Optional[List[str]] = None) -> str:
    """
    Generates a PostgreSQL-safe table identifier and avoids collision with existing tables.
    """
    if existing_tables is None:
        try:
            existing_tables = database.get_tables_list()
        except Exception:
            existing_tables = []

    # Lowercase & sanitize
    clean = str(raw_name).strip().lower()
    clean = re.sub(r'[^a-z0-9_]', '_', clean)
    clean = re.sub(r'_+', '_', clean).strip('_')

    if not clean:
        clean = "dataset_table"
    elif clean[0].isdigit():
        clean = f"ds_{clean}"

    # PostgreSQL max identifier length is 63
    clean = clean[:63].rstrip('_')
    if not clean:
        clean = "dataset_table"

    # Avoid table name collision
    final_table_name = clean
    counter = 2
    existing_lower = [t.lower() for t in existing_tables]
    while final_table_name in existing_lower:
        suffix = f"_{counter}"
        base = clean[:63 - len(suffix)].rstrip('_')
        final_table_name = f"{base}{suffix}"
        counter += 1

    return final_table_name


class SchemaService:
    """Handles schema profiling, type detection, and table name generation."""

    @staticmethod
    def profile_dataset(
        df: pd.DataFrame,
        column_map: Optional[Dict[str, str]] = None
    ) -> List[ColumnProfile]:
        """
        Generates comprehensive column profiling and detected PostgreSQL data types.
        """
        profiles: List[ColumnProfile] = []
        total_rows = len(df)
        rev_map = {v: k for k, v in column_map.items()} if column_map else {}

        for norm_col in df.columns:
            series = df[norm_col]
            orig_name = rev_map.get(norm_col, norm_col)
            detected_type = infer_postgresql_type(series)
            
            null_count = int(series.isna().sum())
            null_pct = round((null_count / total_rows * 100), 2) if total_rows > 0 else 0.0

            # Calculate unique count safely
            non_null = series.dropna()
            unique_count = int(non_null.nunique()) if len(non_null) > 0 else 0

            # Sample value representation
            sample_val = None
            if len(non_null) > 0:
                first_val = non_null.iloc[0]
                sample_val = str(first_val)[:100]

            profiles.append(ColumnProfile(
                original_name=str(orig_name),
                normalized_name=str(norm_col),
                detected_type=detected_type,
                null_count=null_count,
                null_percentage=null_pct,
                unique_count=unique_count,
                sample_value=sample_val
            ))

        return profiles
