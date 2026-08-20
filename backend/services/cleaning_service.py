"""
Data Cleaning Service
Provides transparent, non-destructive data cleaning, whitespace trimming,
exact duplicate removal, empty row/column removal, and column identifier normalization.
"""

import re
from typing import Tuple, Dict, List
import pandas as pd
from backend.schemas.dataset import CleaningReport


def normalize_column_name(col_name: str, existing_names: List[str]) -> str:
    """
    Normalizes a single column name into a safe, valid PostgreSQL identifier.
    Guarantees:
      - Lowercase
      - Alphanumeric and underscores only
      - No starting digits (prefixed with 'col_')
      - Maximum 63 characters (PostgreSQL identifier limit)
      - Unique within the dataset table (appends _2, _3 on collision)
    """
    raw = str(col_name).strip().lower()
    
    # Replace non-alphanumeric chars with underscore
    clean = re.sub(r'[^a-z0-9_]', '_', raw)
    # Collapse multiple consecutive underscores
    clean = re.sub(r'_+', '_', clean).strip('_')
    
    if not clean:
        clean = "col_unnamed"
    elif clean[0].isdigit():
        clean = f"col_{clean}"

    # Truncate to PostgreSQL limit of 63 bytes
    clean = clean[:63].rstrip('_')
    if not clean:
        clean = "col_unnamed"

    # Ensure uniqueness among existing normalized names
    final_name = clean
    counter = 2
    while final_name in existing_names:
        suffix = f"_{counter}"
        base = clean[:63 - len(suffix)].rstrip('_')
        final_name = f"{base}{suffix}"
        counter += 1

    return final_name


class CleaningService:
    """Handles structured tabular data cleaning and reporting."""

    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str], CleaningReport]:
        """
        Performs safe, conservative cleaning on a pandas DataFrame.
        
        Returns:
            Tuple[cleaned_df, column_name_map, CleaningReport]
        """
        df = df.copy()
        rows_before = len(df)
        columns_before = len(df.columns)
        operations: List[str] = []

        # 1. Normalize Column Names
        original_columns = list(df.columns)
        normalized_columns: List[str] = []
        column_map: Dict[str, str] = {}

        for col in original_columns:
            norm = normalize_column_name(str(col), normalized_columns)
            normalized_columns.append(norm)
            column_map[str(col)] = norm

        df.columns = normalized_columns
        cols_normalized_count = sum(1 for o, n in zip(original_columns, normalized_columns) if str(o) != n)
        if cols_normalized_count > 0:
            operations.append(f"Normalized {cols_normalized_count} column identifier(s) to PostgreSQL-safe format.")

        # 2. Remove Completely Empty Columns
        non_empty_cols = df.dropna(how='all', axis=1)
        empty_cols_removed = columns_before - len(non_empty_cols.columns)
        if empty_cols_removed > 0:
            df = non_empty_cols.copy()
            operations.append(f"Removed {empty_cols_removed} completely empty column(s).")

        # 3. Trim Whitespace on String/Text Columns and Standardize Empty Strings to None
        for col in df.columns:
            if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
                # Strip string values
                df[col] = df[col].apply(lambda v: v.strip() if isinstance(v, str) else v)
                # Replace empty strings with None/NaN so PostgreSQL stores NULL
                df[col] = df[col].apply(lambda v: None if (isinstance(v, str) and v == "") else v)

        # 4. Remove Completely Empty Rows (including rows that became empty after whitespace stripping)
        non_empty_rows = df.dropna(how='all', axis=0)
        empty_rows_removed = rows_before - len(non_empty_rows)
        if empty_rows_removed > 0:
            df = non_empty_rows.copy()
            operations.append(f"Removed {empty_rows_removed} completely empty row(s).")

        # 5. Detect and Remove Exact Duplicate Rows (after string standardization)
        duplicate_count = int(df.duplicated().sum())
        if duplicate_count > 0:
            df = df.drop_duplicates()
            operations.append(f"Detected and removed {duplicate_count} exact duplicate row(s).")

        df = df.copy()

        # Count total missing values preserved as NULL
        total_nulls = int(df.isna().sum().sum())
        if total_nulls > 0:
            operations.append(f"Preserved {total_nulls} missing cell value(s) safely as PostgreSQL NULL.")

        # Reset row index
        df = df.reset_index(drop=True)

        rows_after = len(df)
        columns_after = len(df.columns)

        report = CleaningReport(
            rows_before=rows_before,
            rows_after=rows_after,
            columns_before=columns_before,
            columns_after=columns_after,
            duplicate_rows_removed=duplicate_count,
            empty_rows_removed=empty_rows_removed,
            empty_columns_removed=empty_cols_removed,
            columns_normalized=cols_normalized_count,
            null_values_preserved=total_nulls,
            operations_performed=operations
        )

        return df, column_map, report
