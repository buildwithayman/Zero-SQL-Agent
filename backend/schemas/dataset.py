"""
Dataset Management Pydantic Schemas
Models for dataset upload, metadata inspection, listing, deletion, profiling, cleaning,
table ingestion, dynamic schema inspection, automatic prompt suggestions,
and popular dataset hub catalog / recommendations.
"""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


class DatasetMetadataSchema(BaseModel):
    """Full dataset metadata response model."""
    dataset_id: str = Field(description="Unique UUID identifying the dataset")
    dataset_name: str = Field(description="Display name for the dataset")
    original_filename: str = Field(description="Original uploaded filename")
    stored_path: str = Field(description="Safe internal storage path identifier")
    file_format: str = Field(description="Normalized file format (csv, xlsx, json, parquet)")
    file_size_bytes: int = Field(description="Raw file size in bytes")
    file_size_formatted: str = Field(description="Human readable file size string (e.g. 2.4 MB)")
    upload_timestamp: datetime = Field(description="Timestamp when file was uploaded")
    processing_status: str = Field(default="UPLOADED", description="Processing status (UPLOADED, PROCESSING, READY, FAILED, DELETED)")
    uploaded_by: str = Field(default="admin", description="Admin user who uploaded the file")
    table_name: Optional[str] = Field(default=None, description="PostgreSQL destination table name")
    row_count: Optional[int] = Field(default=None, description="Imported row count")
    column_count: Optional[int] = Field(default=None, description="Imported column count")
    suggested_prompts: Optional[List[str]] = Field(default_factory=list, description="AI-generated one-click suggested questions")
    error_message: Optional[str] = Field(default=None, description="Error details if processing failed")


class DatasetUploadResponse(BaseModel):
    """Response returned upon successful dataset upload and validation."""
    status: str = Field(default="success", description="Operation status")
    message: str = Field(description="User-friendly status message")
    dataset: DatasetMetadataSchema = Field(description="Created dataset metadata")


class DatasetListResponse(BaseModel):
    """Response returned when listing all uploaded datasets."""
    total_count: int = Field(description="Total number of uploaded datasets")
    datasets: List[DatasetMetadataSchema] = Field(description="List of dataset metadata objects")


class DatasetDeleteResponse(BaseModel):
    """Response returned upon dataset deletion."""
    status: str = Field(default="success", description="Deletion status")
    message: str = Field(description="Status message")
    deleted_dataset_id: str = Field(description="ID of the deleted dataset")


# ==============================================================================
# Step 3 & 4 Schemas: Profiling, Cleaning, Dynamic Ingestion & Prompts
# ==============================================================================

class ColumnProfile(BaseModel):
    """Profile and detected PostgreSQL type for a single column."""
    original_name: str = Field(description="Original column name before normalization")
    normalized_name: str = Field(description="PostgreSQL-safe lowercase column identifier")
    detected_type: str = Field(description="Inferred PostgreSQL data type (e.g. INTEGER, NUMERIC, DATE, TEXT)")
    null_count: int = Field(default=0, description="Count of missing/null values in column")
    null_percentage: float = Field(default=0.0, description="Percentage of missing values (0-100%)")
    unique_count: int = Field(default=0, description="Number of distinct non-null values")
    sample_value: Optional[str] = Field(default=None, description="Sample non-null representative value")


class CleaningReport(BaseModel):
    """Transparent summary of all data cleaning transformations performed."""
    rows_before: int = Field(description="Total rows before cleaning")
    rows_after: int = Field(description="Total rows after cleaning")
    columns_before: int = Field(description="Total columns before cleaning")
    columns_after: int = Field(description="Total columns after cleaning")
    duplicate_rows_removed: int = Field(default=0, description="Exact duplicate rows dropped")
    empty_rows_removed: int = Field(default=0, description="Completely empty rows dropped")
    empty_columns_removed: int = Field(default=0, description="Completely empty columns dropped")
    columns_normalized: int = Field(default=0, description="Count of normalized column identifiers")
    null_values_preserved: int = Field(default=0, description="Missing values safely preserved as NULL")
    operations_performed: List[str] = Field(default_factory=list, description="List of discrete cleaning operations")


class DatasetPreview(BaseModel):
    """Preview of parsed and cleaned dataset records."""
    total_rows: int = Field(description="Total row count in cleaned dataset")
    total_columns: int = Field(description="Total column count in cleaned dataset")
    preview_rows: int = Field(description="Number of sample rows included in preview")
    columns: List[str] = Field(description="List of normalized column names")
    records: List[Dict[str, Any]] = Field(description="First N rows formatted as list of key-value dictionaries")


class DatasetProcessResponse(BaseModel):
    """Response returned after parsing, profiling, and cleaning a dataset."""
    status: str = Field(default="ready_for_import", description="Status code indicating dataset is ready for import")
    dataset_id: str = Field(description="UUID of the processed dataset")
    dataset_name: str = Field(description="Dataset display name")
    suggested_table_name: str = Field(description="Safe suggested PostgreSQL destination table name")
    preview: DatasetPreview = Field(description="Tabular preview of dataset")
    schema_detected: List[ColumnProfile] = Field(description="Detected schema with types and null counts")
    cleaning_report: CleaningReport = Field(description="Transparent cleaning report")
    suggested_prompts: Optional[List[str]] = Field(default_factory=list, description="Suggested questions preview")


class DatasetImportRequest(BaseModel):
    """Request payload to trigger explicit table creation and data import."""
    custom_table_name: Optional[str] = Field(default=None, description="Optional custom destination table name")


class DatasetImportResponse(BaseModel):
    """Response returned upon successful table creation and bulk data import."""
    status: str = Field(default="success", description="Import operation status")
    message: str = Field(description="Status confirmation message")
    dataset_id: str = Field(description="Dataset UUID")
    table_name: str = Field(description="Created PostgreSQL table name")
    rows_imported: int = Field(description="Exact count of rows inserted into PostgreSQL")
    columns_imported: int = Field(description="Count of columns created in table")
    suggested_prompts: List[str] = Field(default_factory=list, description="Automatically generated prompt suggestions for this dataset")


class DatasetPromptsResponse(BaseModel):
    """Response model for dataset suggested analytical questions."""
    dataset_id: str = Field(description="UUID of dataset")
    dataset_name: str = Field(description="Display name of dataset")
    table_name: Optional[str] = Field(default=None, description="PostgreSQL table name")
    suggested_prompts: List[str] = Field(default_factory=list, description="One-click analytical questions")


class DatasetSchemaResponse(BaseModel):
    """Response model for live dataset table schema."""
    dataset_id: str = Field(description="UUID of dataset")
    dataset_name: str = Field(description="Display name of dataset")
    table_name: str = Field(description="PostgreSQL table name")
    columns: List[ColumnProfile] = Field(description="List of column profiles")


# ==============================================================================
# Step 5 Schemas: Popular Dataset Hub & Recommendations
# ==============================================================================

class CatalogDatasetSchema(BaseModel):
    """Represents a curated, popular dataset available in the Dataset Hub catalog."""
    catalog_id: str = Field(description="Unique catalog identifier (e.g. 'superstore_sales')")
    name: str = Field(description="Display name for the dataset")
    description: str = Field(description="Short description of contents and analytical use cases")
    category: str = Field(description="Domain category (Sales, E-commerce, Customer Analytics, Finance, HR, Sports, Entertainment, General Analytics)")
    source_name: str = Field(description="Provider / repository name (e.g. 'Tableau Community', 'Kaggle Open Data')")
    source_url: str = Field(description="Transparent web reference link to the original source")
    download_url: Optional[str] = Field(default=None, description="Direct download URL or embedded source identifier")
    file_format: str = Field(default="csv", description="Format (csv, xlsx, json, parquet)")
    approx_size: str = Field(default="< 1 MB", description="Approximate human-readable size")
    approx_rows: int = Field(default=0, description="Approximate row count")
    tags: List[str] = Field(default_factory=list, description="Search and recommendation tags")
    analytics_topics: List[str] = Field(default_factory=list, description="Key metrics and analytics topics covered")
    is_imported: bool = Field(default=False, description="Whether this dataset is already imported and ready in PostgreSQL")
    imported_dataset_id: Optional[str] = Field(default=None, description="Active dataset ID if imported")
    imported_table_name: Optional[str] = Field(default=None, description="Active table name in PostgreSQL if imported")


class CatalogListResponse(BaseModel):
    """Response model for popular dataset catalog listing."""
    total_count: int = Field(description="Total catalog datasets available")
    categories: List[str] = Field(description="All available categories")
    datasets: List[CatalogDatasetSchema] = Field(description="List of catalog dataset objects")


class CategoryInfo(BaseModel):
    """Summary information for a single dataset category."""
    name: str = Field(description="Category name")
    count: int = Field(description="Number of datasets in category")
    icon: str = Field(description="Visual emoji icon")


class CategoryListResponse(BaseModel):
    """Response model for category breakdown."""
    total_categories: int = Field(description="Total number of distinct categories")
    categories: List[CategoryInfo] = Field(description="Category details with dataset counts")


class DatasetRecommendationRequest(BaseModel):
    """Request payload for AI dataset recommendation."""
    query: str = Field(description="User prompt or intent (e.g. 'I want to practice sales and profit analytics')")
    category: Optional[str] = Field(default=None, description="Optional category filter")
    limit: int = Field(default=5, description="Maximum recommendations to return")


class DatasetRecommendationResponse(BaseModel):
    """Response model for AI dataset recommendation."""
    query: str = Field(description="User input query")
    recommended_datasets: List[CatalogDatasetSchema] = Field(description="Ranked list of matching catalog datasets")
    reasoning: Optional[str] = Field(default=None, description="Explanation of why these datasets were recommended")


class UseCatalogDatasetResponse(BaseModel):
    """Response model after user clicks 'Use Dataset' on a catalog entry."""
    status: str = Field(default="success", description="Status code")
    message: str = Field(description="Confirmation message")
    dataset_id: str = Field(description="Dataset UUID in dataset_metadata")
    table_name: str = Field(description="PostgreSQL destination table name")
    rows_imported: int = Field(description="Total rows imported")
    suggested_prompts: List[str] = Field(default_factory=list, description="One-click questions generated by PromptService")
    was_reused: bool = Field(default=False, description="True if existing READY table was reused without re-downloading")
