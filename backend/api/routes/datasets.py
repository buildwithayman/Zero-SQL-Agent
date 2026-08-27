"""
Admin & Public Dataset Management Routes
Handles secure file upload, listing, details inspection, dataset deletion,
data profiling, data cleaning, dynamic PostgreSQL table ingestion, prompt suggestions,
and the Popular Dataset Hub catalog & AI recommendations.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, Query, Request
import database
from backend.config import Settings, get_settings
from backend.limiter import limiter

logger = logging.getLogger("zerosql")
from backend.services.auth_service import get_current_admin
from backend.services.storage_service import StorageService
from backend.services.dataset_service import DatasetService
from backend.services.ingestion_service import IngestionService
from backend.services.prompt_service import PromptService
from backend.services.schema_service import SchemaService
from backend.services.dataset_catalog_service import DatasetCatalogService
from backend.services.dataset_recommendation_service import DatasetRecommendationService
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
    ColumnProfile,
    CatalogDatasetSchema,
    CatalogListResponse,
    CategoryListResponse,
    DatasetRecommendationRequest,
    DatasetRecommendationResponse,
    UseCatalogDatasetResponse
)

router = APIRouter(prefix="/admin/datasets", tags=["Admin Datasets"])
public_router = APIRouter(prefix="/datasets", tags=["Public Datasets"])


# ==============================================================================
# Admin Routes (Requires Authentication)
# ==============================================================================

@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload New Dataset",
    description="Validates and securely persists a dataset (CSV, XLSX, JSON, Parquet) with metadata tracking."
)
@limiter.limit("5/minute")
async def upload_dataset(
    request: Request,
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

    # 2. Determine dataset name
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
        storage.delete_stored_file(stored_path)
        logger.error(f"Database metadata recording failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database metadata recording failed due to an internal server error."
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
    """Admin-only dataset listing endpoint."""
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
    """Admin-only dataset detail endpoint."""
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
    description="Safely drops physical dynamic table, removes dataset file from storage, and deletes metadata record from PostgreSQL."
)
def delete_dataset(
    dataset_id: str,
    admin_user: str = Depends(get_current_admin),
    settings: Settings = Depends(get_settings)
) -> DatasetDeleteResponse:
    """Admin-only dataset deletion endpoint."""
    dataset_svc = DatasetService(settings)
    existing = dataset_svc.get_dataset_by_id(dataset_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found."
        )

    try:
        success, dropped_table = dataset_svc.delete_dataset(dataset_id)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(val_err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dataset '{dataset_id}': {str(err)}"
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dataset '{dataset_id}'."
        )

    table_msg = f" and dropped table '{dropped_table}'" if dropped_table else ""
    return DatasetDeleteResponse(
        status="success",
        message=f"Dataset '{existing.dataset_name}' ({dataset_id}) deleted successfully{table_msg}.",
        deleted_dataset_id=dataset_id,
        dropped_table_name=dropped_table
    )


@router.post(
    "/{dataset_id}/process",
    response_model=DatasetProcessResponse,
    summary="Process, Clean, and Profile Dataset",
    description="Parses dataset, performs non-destructive cleaning, detects schema types, and returns preview and cleaning report."
)
@limiter.limit("5/minute")
def process_dataset(
    request: Request,
    dataset_id: str,
    admin_user: str = Depends(get_current_admin),
    settings: Settings = Depends(get_settings)
) -> DatasetProcessResponse:
    """Admin-only dataset processing endpoint."""
    ingestion_svc = IngestionService(settings)
    return ingestion_svc.process_dataset(dataset_id)


@router.post(
    "/{dataset_id}/import",
    response_model=DatasetImportResponse,
    summary="Create PostgreSQL Table and Import Data",
    description="Executes explicit, transactional table creation and bulk insertion for the cleaned dataset."
)
@limiter.limit("5/minute")
def import_dataset(
    request: Request,
    dataset_id: str,
    payload: Optional[DatasetImportRequest] = None,
    admin_user: str = Depends(get_current_admin),
    settings: Settings = Depends(get_settings)
) -> DatasetImportResponse:
    """Admin-only explicit confirmation endpoint."""
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
# Public Dataset Hub Routes (Read-Only & Catalog Ingestion)
# ==============================================================================

@public_router.get(
    "/catalog",
    response_model=CatalogListResponse,
    summary="List Popular Catalog Datasets",
    description="Returns curated popular datasets across domains with live PostgreSQL import status."
)
@limiter.limit("60/minute")
def list_popular_catalog(
    request: Request,
    category: Optional[str] = Query(None, description="Optional category filter"),
    settings: Settings = Depends(get_settings)
) -> CatalogListResponse:
    """Public endpoint to browse popular dataset catalog."""
    catalog_svc = DatasetCatalogService(settings)
    datasets = catalog_svc.list_catalog_datasets(category=category)
    all_categories = [c.name for c in catalog_svc.list_categories()]
    return CatalogListResponse(
        total_count=len(datasets),
        categories=all_categories,
        datasets=datasets
    )


@public_router.get(
    "/catalog/categories",
    response_model=CategoryListResponse,
    summary="List Dataset Categories",
    description="Returns distinct dataset categories with dataset counts and visual icons."
)
def list_catalog_categories(
    settings: Settings = Depends(get_settings)
) -> CategoryListResponse:
    """Public endpoint to list categories."""
    catalog_svc = DatasetCatalogService(settings)
    categories = catalog_svc.list_categories()
    return CategoryListResponse(
        total_categories=len(categories),
        categories=categories
    )


@public_router.get(
    "/catalog/{catalog_id}",
    response_model=CatalogDatasetSchema,
    summary="Get Catalog Dataset Details",
    description="Returns detailed metadata and analytics topics for a specific catalog dataset."
)
def get_catalog_dataset_details(
    catalog_id: str,
    settings: Settings = Depends(get_settings)
) -> CatalogDatasetSchema:
    """Public endpoint to inspect catalog dataset details."""
    catalog_svc = DatasetCatalogService(settings)
    datasets = catalog_svc.list_catalog_datasets()
    for ds in datasets:
        if ds.catalog_id.lower() == catalog_id.lower():
            return ds
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Catalog dataset '{catalog_id}' not found."
    )


@public_router.post(
    "/catalog/{catalog_id}/use",
    response_model=UseCatalogDatasetResponse,
    summary="Use Popular Dataset",
    description="Retrieves a catalog dataset, processes it through the unified ingestion pipeline, and makes it AI-ready."
)
def use_catalog_dataset_endpoint(
    catalog_id: str,
    settings: Settings = Depends(get_settings)
) -> UseCatalogDatasetResponse:
    """
    Public 'Use Dataset' endpoint.
    Reuses existing storage, cleaning, schema, ingestion, and prompt services.
    Avoids duplicate downloads and tables via catalog deduplication.
    """
    catalog_svc = DatasetCatalogService(settings)
    return catalog_svc.use_catalog_dataset(catalog_id)


@public_router.post(
    "/recommendations",
    response_model=DatasetRecommendationResponse,
    summary="AI Dataset Recommendations",
    description="Recommends relevant catalog datasets based on user prompt, intent, or keywords."
)
def recommend_datasets_endpoint(
    payload: DatasetRecommendationRequest,
    settings: Settings = Depends(get_settings)
) -> DatasetRecommendationResponse:
    """Public endpoint for natural language dataset recommendations."""
    rec_svc = DatasetRecommendationService(settings)
    return rec_svc.recommend_datasets(
        query=payload.query,
        category=payload.category,
        limit=payload.limit
    )


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
