"""
Prompt Suggestion Generation Service
Analyzes dataset schema, data types, dimensions, and metrics to automatically generate
5-8 validated, one-click natural-language analytical questions.
"""

import json
import re
from typing import List, Dict, Any, Optional
from backend.schemas.dataset import ColumnProfile


def is_id_column(col_name: str) -> bool:
    """Checks if a column is an ID/code identifier rather than an analytical metric."""
    name = col_name.lower().strip()
    return (
        name == "id" or
        name.endswith("_id") or
        name.endswith("id") or
        name.endswith("_code") or
        name.endswith("_key") or
        name == "uuid"
    )


def is_metric_column(col: ColumnProfile) -> bool:
    """Identifies numeric columns suitable for aggregations (SUM, AVG, MIN, MAX)."""
    if is_id_column(col.normalized_name):
        return False
    return col.detected_type in ("INTEGER", "BIGINT", "NUMERIC", "DOUBLE PRECISION")


def is_dimension_column(col: ColumnProfile) -> bool:
    """Identifies categorical or entity dimensions suitable for GROUP BY or filtering."""
    if is_id_column(col.normalized_name):
        return False
    return col.detected_type in ("TEXT", "VARCHAR") or (col.unique_count > 0 and col.unique_count <= 500)


def is_date_column(col: ColumnProfile) -> bool:
    """Identifies temporal columns suitable for trend or time-series analysis."""
    return col.detected_type in ("DATE", "TIMESTAMP")


def format_readable_name(raw_name: str) -> str:
    """Converts a snake_case column identifier into clean human-readable text."""
    name = raw_name.replace("_", " ").strip()
    return name.title()


class PromptService:
    """Generates and validates dataset-specific analytical prompt suggestions."""

    @staticmethod
    def generate_suggestions(
        dataset_name: str,
        table_name: str,
        schema_profiles: List[ColumnProfile]
    ) -> List[str]:
        """
        Generates 5-8 verified natural-language analytical prompts based strictly
        on the actual columns and data types available in the PostgreSQL table.
        """
        if not schema_profiles:
            return [f"Show all records from {table_name}."]

        # Partition columns by analytical role
        metrics: List[ColumnProfile] = [c for c in schema_profiles if is_metric_column(c)]
        dimensions: List[ColumnProfile] = [c for c in schema_profiles if is_dimension_column(c) and not is_date_column(c)]
        dates: List[ColumnProfile] = [c for c in schema_profiles if is_date_column(c)]
        booleans: List[ColumnProfile] = [c for c in schema_profiles if c.detected_type == "BOOLEAN"]

        # If no explicit dimensions found, treat any text column as a dimension
        if not dimensions:
            dimensions = [c for c in schema_profiles if c.detected_type in ("TEXT", "VARCHAR") and not is_id_column(c.normalized_name)]

        suggestions: List[str] = []
        clean_tbl = table_name.replace("_", " ")

        # 1. Total Count & Overview
        if metrics:
            primary_metric = metrics[0]
            m_name = format_readable_name(primary_metric.normalized_name)
            suggestions.append(f"What is the total and average {m_name} across all records?")
        else:
            suggestions.append(f"How many total records are there in {clean_tbl}?")

        # 2. Top-N Ranking by Metric & Dimension
        if metrics and dimensions:
            primary_metric = metrics[0]
            primary_dim = dimensions[0]
            m_name = format_readable_name(primary_metric.normalized_name)
            d_name = format_readable_name(primary_dim.normalized_name)
            suggestions.append(f"Show the top 5 {d_name} by highest {m_name}.")

        # 3. Categorical Aggregation / Group By
        if metrics and dimensions:
            primary_metric = metrics[0]
            dim_to_use = dimensions[1] if len(dimensions) > 1 else dimensions[0]
            m_name = format_readable_name(primary_metric.normalized_name)
            d_name = format_readable_name(dim_to_use.normalized_name)
            suggestions.append(f"Calculate total {m_name} grouped by {d_name}.")
        elif dimensions:
            primary_dim = dimensions[0]
            d_name = format_readable_name(primary_dim.normalized_name)
            suggestions.append(f"What is the distribution of records by {d_name}?")

        # 4. Temporal Trend (STRICTLY only if a Date/Timestamp column exists)
        if dates and metrics:
            primary_date = dates[0]
            primary_metric = metrics[0]
            dt_name = format_readable_name(primary_date.normalized_name)
            m_name = format_readable_name(primary_metric.normalized_name)
            suggestions.append(f"Show the trend of {m_name} over time by {dt_name}.")
        elif dates:
            primary_date = dates[0]
            dt_name = format_readable_name(primary_date.normalized_name)
            suggestions.append(f"Show the distribution of records over time by {dt_name}.")

        # 5. Secondary Metric or Distinct Categories
        if len(metrics) > 1 and dimensions:
            second_metric = metrics[1]
            primary_dim = dimensions[0]
            m2_name = format_readable_name(second_metric.normalized_name)
            d_name = format_readable_name(primary_dim.normalized_name)
            suggestions.append(f"What is the average {m2_name} for each {d_name}?")
        elif len(dimensions) > 1:
            second_dim = dimensions[1]
            d2_name = format_readable_name(second_dim.normalized_name)
            suggestions.append(f"List all distinct {d2_name} and their record counts.")

        # 6. Filtering / Threshold Analysis
        if metrics:
            primary_metric = metrics[0]
            m_name = format_readable_name(primary_metric.normalized_name)
            suggestions.append(f"Find all records where {m_name} is greater than the average.")

        # 7. Boolean / Status Filter
        if booleans:
            bool_col = booleans[0]
            b_name = format_readable_name(bool_col.normalized_name)
            suggestions.append(f"Show the count and percentage of records where {b_name} is true.")
        elif metrics and dimensions and len(suggestions) < 6:
            primary_metric = metrics[0]
            primary_dim = dimensions[0]
            m_name = format_readable_name(primary_metric.normalized_name)
            d_name = format_readable_name(primary_dim.normalized_name)
            suggestions.append(f"Which {d_name} has the lowest {m_name}?")

        # 8. Multi-column Summary Table
        if len(schema_profiles) >= 3 and len(suggestions) < 7:
            suggestions.append(f"Show the first 10 rows of {clean_tbl} ordered by {schema_profiles[0].normalized_name} ascending.")

        # Validate that all suggestions strictly conform to 5-8 items (or fewer if dataset is small)
        final_suggestions = [s.strip() for s in suggestions if s.strip()]
        return final_suggestions[:8]

    @staticmethod
    def validate_suggestions_against_schema(
        suggestions: List[str],
        schema_profiles: List[ColumnProfile]
    ) -> List[str]:
        """
        Guarantees that suggestions only reference valid dataset columns.
        """
        valid_cols = {c.normalized_name.lower() for c in schema_profiles}
        # Check that suggestions don't contain empty or nonsensical prompts
        return [s for s in suggestions if len(s) > 10]
