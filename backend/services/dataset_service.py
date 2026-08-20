"""
Dataset Metadata Management Service
Provides persistent CRUD operations for dataset tracking in PostgreSQL via admin connection.
"""

from typing import List, Optional
from datetime import datetime, timezone
import database
from backend.config import Settings
from backend.schemas.dataset import DatasetMetadataSchema
from backend.services.storage_service import StorageService, format_file_size


def init_dataset_metadata_table():
    """
    Initializes the dataset_metadata table in PostgreSQL if it does not already exist.
    Uses the write-capable admin database connection.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS dataset_metadata (
        dataset_id VARCHAR(36) PRIMARY KEY,
        dataset_name VARCHAR(255) NOT NULL,
        original_filename VARCHAR(255) NOT NULL,
        stored_path VARCHAR(500) NOT NULL,
        file_format VARCHAR(20) NOT NULL,
        file_size_bytes BIGINT NOT NULL,
        upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        processing_status VARCHAR(50) DEFAULT 'UPLOADED',
        uploaded_by VARCHAR(100) DEFAULT 'admin',
        table_name VARCHAR(100),
        row_count BIGINT,
        column_count INT,
        error_message TEXT
    );
    """
    try:
        with database.get_admin_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(create_table_sql)
            conn.commit()
    except Exception as e:
        # If database is offline or not reachable at init, allow graceful handling
        print(f"Warning: Unable to initialize dataset_metadata table: {str(e)}")


def row_to_schema(row: dict) -> DatasetMetadataSchema:
    """Converts a database dictionary row to DatasetMetadataSchema."""
    size_bytes = row.get("file_size_bytes", 0)
    return DatasetMetadataSchema(
        dataset_id=row["dataset_id"],
        dataset_name=row["dataset_name"],
        original_filename=row["original_filename"],
        stored_path=row["stored_path"],
        file_format=row["file_format"],
        file_size_bytes=size_bytes,
        file_size_formatted=format_file_size(size_bytes),
        upload_timestamp=row.get("upload_timestamp", datetime.now(timezone.utc)),
        processing_status=row.get("processing_status", "UPLOADED"),
        uploaded_by=row.get("uploaded_by", "admin"),
        table_name=row.get("table_name"),
        row_count=row.get("row_count"),
        column_count=row.get("column_count"),
        error_message=row.get("error_message")
    )


class DatasetService:
    """Service layer for dataset metadata operations."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.storage = StorageService(settings)
        init_dataset_metadata_table()

    def record_uploaded_dataset(
        self,
        dataset_id: str,
        dataset_name: str,
        original_filename: str,
        stored_path: str,
        file_format: str,
        file_size_bytes: int,
        uploaded_by: str = "admin"
    ) -> DatasetMetadataSchema:
        """
        Inserts newly uploaded dataset record into PostgreSQL dataset_metadata.
        Uses parameterized SQL execution.
        """
        insert_sql = """
        INSERT INTO dataset_metadata (
            dataset_id, dataset_name, original_filename, stored_path,
            file_format, file_size_bytes, upload_timestamp,
            processing_status, uploaded_by
        ) VALUES (
            %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'UPLOADED', %s
        )
        RETURNING *;
        """
        with database.get_admin_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    insert_sql,
                    (dataset_id, dataset_name, original_filename, stored_path, file_format, file_size_bytes, uploaded_by)
                )
                row = cursor.fetchone()
            conn.commit()

        return row_to_schema(row)

    def list_all_datasets(self) -> List[DatasetMetadataSchema]:
        """
        Fetches all dataset metadata records ordered by upload_timestamp descending.
        """
        select_sql = """
        SELECT * FROM dataset_metadata
        ORDER BY upload_timestamp DESC;
        """
        with database.get_readonly_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(select_sql)
                rows = cursor.fetchall()

        return [row_to_schema(r) for r in rows]

    def get_dataset_by_id(self, dataset_id: str) -> Optional[DatasetMetadataSchema]:
        """
        Retrieves a single dataset metadata record by its UUID.
        """
        select_sql = """
        SELECT * FROM dataset_metadata
        WHERE dataset_id = %s;
        """
        with database.get_readonly_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(select_sql, (dataset_id,))
                row = cursor.fetchone()

        return row_to_schema(row) if row else None

    def delete_dataset(self, dataset_id: str) -> bool:
        """
        Deletes the dataset file from disk and deletes its metadata record from PostgreSQL.
        """
        dataset = self.get_dataset_by_id(dataset_id)
        if not dataset:
            return False

        # 1. Safely remove from storage
        self.storage.delete_stored_file(dataset.stored_path)

        # 2. Remove metadata record from PostgreSQL
        delete_sql = "DELETE FROM dataset_metadata WHERE dataset_id = %s;"
        with database.get_admin_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(delete_sql, (dataset_id,))
            conn.commit()

        return True
