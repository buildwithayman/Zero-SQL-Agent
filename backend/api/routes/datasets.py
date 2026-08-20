"""
Admin Dataset Management Routes
Handles secure file upload, listing, details inspection, dataset deletion,
data profiling, data cleaning, dynamic PostgreSQL table ingestion, and prompt suggestions.
"""

from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
import database
from backend.config import Settings, get_settings
from backend.services.auth_service import get_current_admin
from backend.services.storage_service import StorageService
from backend.services.dataset_service import DatasetService
from backend.services.ingestion_service import IngestionService
from backend.services.prompt_service import PromptService
from backend.services.schema_service import SchemaService
from backend.schemas.dataset import (
    DatasetMetadataSchema,
    DatasetUploadResponse,
    DatasetListResponse,
    DatasetDeleteResponse,
    DatasetProcessResponse,
    DatasetImportRequest,
    DatasetImportResponse,
    DatasetPromptsResponse,
    DatasetSchemaResponse,
    ColumnProfile
)

router = APIRouter(prefix="/admin/datasets", tags=["Admin Datasets"])
public_router = APIRouter(prefix="/datasets", tags=["Public Datasets"])


@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload New Dataset",
    description="Validates and securely persists a dataset (CSV, XLSX, JSON, Parquet) with metadata tracking."
)
async def upload_dataset(
    file: UploadFile = File(..., description="Dataset file (CSV, XLSX, JSON, Parquet)"),
    dataset_name: Optional[str] = Form(None, description="Optional custom name for the dataset"),
    admin_user: str = Depends(get_current_admin),
    settings: Settings = Depends(get_settings)
) -> DatasetUploadResponse:
    """
    Admin-only file upload endpoint.
    Validates file format, size, content structure, saves safely to disk,
    and inserts metadata into PostgreSQL.
    """
    storage = StorageService(settings)
    dataset_svc = DatasetService(settings)

    # 1. Validate and store file safely
    dataset_id, original_filename, stored_path, file_size, ext = await storage.save_uploaded_file(file)

    # 2. Determine dataset name (use custom name or clean original filename without extension)
    effective_name = dataset_name.strip() if dataset_name and dataset_name.strip() else original_filename.rsplit(".", 1)[0]

    # 3. Record in PostgreSQL dataset_metadata
    try:
        dataset_record = dataset_svc.record_uploaded_dataset(
            dataset_id=dataset_id,
            dataset_name=effective_name,
            original_filename=original_filename,
            stored_path=stored_path,
            file_format=ext,
            file_size_bytes=file_size,
            uploaded_by=admin_user
        )
    except Exception as e:
        # Clean up stored file if database write failed
        storage.delete_stored_file(stored_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database metadata recording failed: {str(e)}"
        )

    return DatasetUploadResponse(
        status="success",
        message=f"Dataset '{effective_name}' ({ext.upper()}) uploaded and validated successfully.",
        dataset=dataset_record
    )


@router.get(
    "",
    response_model=DatasetListResponse,
    summary="List All Uploaded Datasets",
    description="Returns metadata of all uploaded datasets ordered by upload timestamp."
)
def list_datasets(
    admin_user: str = Depends(get_current_admin),
    settings: Settings = Depends(get_settings)
) -> DatasetListResponse:
    """
    Admin-only dataset listing endpoint.
    """
    dataset_svc = DatasetService(settings)
    datasets = dataset_svc.list_all_datasets()
    return DatasetListResponse(
        total_count=len(datasets),
        datasets=datasets
    )


@router.get(
    "/{dataset_id}",
    response_model=DatasetMetadataSchema,
    summary="Get Dataset Details",
    description="Retrieves metadata details for a specific dataset."
)
def get_dataset_details(
    dataset_id: str,
    admin_user: str = Depends(get_current_admin),
    settings: Settings = Depends(get_settings)
) -> DatasetMetadataSchema:
    """
    Admin-only dataset detail endpoint.
    """
    dataset_svc = DatasetService(settings)
    dataset = dataset_svc.get_dataset_by_id(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found."
        )
    return dataset


@router.delete(
    "/{dataset_id}",
    response_model=DatasetDeleteResponse,
    summary="Delete Dataset",
    description="Safely removes dataset file from storage and removes metadata record from PostgreSQL."
)
def delete_dataset(
    dataset_id: str,
    admin_user: str = Depends(get_current_admin),
    settings: Settings = Depends(get_settings)
) -> DatasetDeleteResponse:
    """
    Admin-only dataset deletion endpoint.
    """
    dataset_svc = DatasetService(settings)
    existing = dataset_svc.get_dataset_by_id(dataset_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found."
        )

    success = dataset_svc.delete_dataset(dataset_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dataset '{dataset_id}'."
        )

    return DatasetDeleteResponse(
        status="success",
        message=f"Dataset '{existing.dataset_name}' ({dataset_id}) deleted successfully.",
        deleted_dataset_id=dataset_id
    )


@router.post(
    "/{dataset_id}/process",
    response_model=DatasetProcessResponse,
    summary="Process, Clean, and Profile Dataset",
    description="Parses dataset, performs non-destructive cleaning, detects schema types, and returns preview and cleaning report."
)
def process_dataset(
    dataset_id: str,
    admin_user: str = Depends(get_current_admin),
    settings: Settings = Depends(get_settings)
) -> DatasetProcessResponse:
    """
    Admin-only dataset processing endpoint.
    Generates preview, cleaning report, and detected schema without modifying the database.
    """
    ingestion_svc = IngestionService(settings)
    return ingestion_svc.process_dataset(dataset_id)


@router.post(
    "/{dataset_id}/import",
    response_model=DatasetImportResponse,
    summary="Create PostgreSQL Table and Import Data",
    description="Executes explicit, transactional table creation and bulk insertion for the cleaned dataset."
)
def import_dataset(
    dataset_id: str,
    payload: Optional[DatasetImportRequest] = None,
    admin_user: str = Depends(get_current_admin),
    settings: Settings = Depends(get_settings)
) -> DatasetImportResponse:
    """
    Admin-only explicit confirmation endpoint.
    Dynamically creates table in PostgreSQL and imports cleaned records transactionally.
    """
    ingestion_svc = IngestionService(settings)
    custom_table = payload.custom_table_name if payload else None
    return ingestion_svc.import_dataset_to_database(dataset_id, custom_table_name=custom_table)


@router.post(
    "/{dataset_id}/prompts/regenerate",
    response_model=DatasetPromptsResponse,
    summary="Regenerate Prompt Suggestions",
    description="Regenerates analytical question suggestions based on live table schema."
)
def regenerate_dataset_prompts(
    dataset_id: str,
    admin_user: str = Depends(get_current_admin),
    settings: Settings = Depends(get_settings)
) -> DatasetPromptsResponse:
    """Admin-only endpoint to regenerate prompt suggestions from live PostgreSQL table."""
    dataset_svc = DatasetService(settings)
    dataset = dataset_svc.get_dataset_by_id(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found."
        )

    if not dataset.table_name or dataset.processing_status != "READY":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset table has not been created yet."
        )

    # Fetch live column information from PostgreSQL
    table_cols = database.get_table_details(dataset.table_name)
    profiles = [
        ColumnProfile(
            original_name=c["column_name"],
            normalized_name=c["column_name"],
            detected_type=c["data_type"].upper(),
            null_count=0,
            null_percentage=0.0,
            unique_count=10,
            sample_value=None
        )
        for c in table_cols
    ]

    new_prompts = PromptService.generate_suggestions(
        dataset_name=dataset.dataset_name,
        table_name=dataset.table_name,
        schema_profiles=profiles
    )

    # Update metadata
    dataset_svc.update_dataset_status(
        dataset_id=dataset_id,
        processing_status=dataset.processing_status,
        suggested_prompts=new_prompts
    )

    return DatasetPromptsResponse(
        dataset_id=dataset_id,
        dataset_name=dataset.dataset_name,
        table_name=dataset.table_name,
        suggested_prompts=new_prompts
    )


# ==============================================================================
# Public Dataset Endpoints (Read-Only)
# ==============================================================================

@public_router.get(
    "/{dataset_id}/prompts",
    response_model=DatasetPromptsResponse,
    summary="Get Dataset Prompt Suggestions",
    description="Returns pre-computed or on-demand one-click analytical questions for a dataset."
)
def get_dataset_prompts(
    dataset_id: str,
    settings: Settings = Depends(get_settings)
) -> DatasetPromptsResponse:
    """Public read endpoint to fetch suggested prompts for active dataset."""
    dataset_svc = DatasetService(settings)
    dataset = dataset_svc.get_dataset_by_id(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found."
        )

    prompts = dataset.suggested_prompts or []
    # If no stored prompts but table exists, generate on demand
    if not prompts and dataset.table_name and dataset.processing_status == "READY":
        table_cols = database.get_table_details(dataset.table_name)
        profiles = [
            ColumnProfile(
                original_name=c["column_name"],
                normalized_name=c["column_name"],
                detected_type=c["data_type"].upper(),
                null_count=0,
                null_percentage=0.0,
                unique_count=10,
                sample_value=None
            )
            for c in table_cols
        ]
        prompts = PromptService.generate_suggestions(
            dataset_name=dataset.dataset_name,
            table_name=dataset.table_name,
            schema_profiles=profiles
        )
        dataset_svc.update_dataset_status(
            dataset_id=dataset_id,
            processing_status=dataset.processing_status,
            suggested_prompts=prompts
        )

    return DatasetPromptsResponse(
        dataset_id=dataset_id,
        dataset_name=dataset.dataset_name,
        table_name=dataset.table_name,
        suggested_prompts=prompts
    )


@public_router.get(
    "/{dataset_id}/schema",
    response_model=DatasetSchemaResponse,
    summary="Get Dataset Live Schema",
    description="Returns column details from live PostgreSQL table."
)
def get_dataset_schema(
    dataset_id: str,
    settings: Settings = Depends(get_settings)
) -> DatasetSchemaResponse:
    """Public read endpoint to inspect live PostgreSQL column schema for a dataset."""
    dataset_svc = DatasetService(settings)
    dataset = dataset_svc.get_dataset_by_id(dataset_id)
    if not dataset or not dataset.table_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' or its PostgreSQL table does not exist."
        )

    table_cols = database.get_table_details(dataset.table_name)
    profiles = [
        ColumnProfile(
            original_name=c["column_name"],
            normalized_name=c["column_name"],
            detected_type=c["data_type"].upper(),
            null_count=0,
            null_percentage=0.0,
            unique_count=0,
            sample_value=None
        )
        for c in table_cols
    ]

    return DatasetSchemaResponse(
        dataset_id=dataset_id,
        dataset_name=dataset.dataset_name,
        table_name=dataset.table_name,
        columns=profiles
    )
