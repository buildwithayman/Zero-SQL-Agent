"""
Dataset Management Pydantic Schemas
Models for dataset upload, metadata inspection, listing, and deletion.
"""

from datetime import datetime
from typing import Optional, List
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
    processing_status: str = Field(default="UPLOADED", description="Processing status (UPLOADED, VALIDATED, FAILED, DELETED)")
    uploaded_by: str = Field(default="admin", description="Admin user who uploaded the file")
    table_name: Optional[str] = Field(default=None, description="PostgreSQL destination table name (Nullable until Step 3 ingestion)")
    row_count: Optional[int] = Field(default=None, description="Row count (Nullable until Step 3 profiling)")
    column_count: Optional[int] = Field(default=None, description="Column count (Nullable until Step 3 profiling)")
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
