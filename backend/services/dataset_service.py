"""
Dataset Metadata Management Service
Provides persistent CRUD operations for dataset tracking in PostgreSQL via admin connection.
"""

import os
import json
import re
import logging
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from psycopg import sql
import database
from backend.config import Settings
from backend.schemas.dataset import DatasetMetadataSchema
from backend.services.storage_service import StorageService, format_file_size

logger = logging.getLogger("zerosql")


# Immutable set of protected production tables that can NEVER be dropped via dataset cleanup
PROTECTED_SYSTEM_TABLES = frozenset({
    "departments", "users", "students", "products", "employees", "orders",
    "superstore_sales", "customer_churn_analytics", "hr_workforce_analytics",
    "supply_chain_logistics", "crypto_market_finance", "dataset_metadata"
})


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
        suggested_prompts TEXT,
        error_message TEXT
    );
    """
    alter_sql = """
    ALTER TABLE dataset_metadata ADD COLUMN IF NOT EXISTS suggested_prompts TEXT;
    """
    try:
        with database.get_admin_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(create_table_sql)
                cursor.execute(alter_sql)
            conn.commit()
    except Exception as e:
        # If database is offline or not reachable at init, allow graceful handling
        print(f"Warning: Unable to initialize dataset_metadata table: {str(e)}")


def row_to_schema(row: dict) -> DatasetMetadataSchema:
    """Helper to convert database dict_row to DatasetMetadataSchema."""
    prompts_raw = row.get("suggested_prompts")
    prompts = []
    if prompts_raw:
        try:
            prompts = json.loads(prompts_raw) if isinstance(prompts_raw, str) else prompts_raw
        except Exception:
            prompts = []

    ts = row.get("upload_timestamp")
    if ts and ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    return DatasetMetadataSchema(
        dataset_id=row["dataset_id"],
        dataset_name=row["dataset_name"],
        original_filename=row["original_filename"],
        stored_path=row["stored_path"],
        file_format=row["file_format"],
        file_size_bytes=row["file_size_bytes"],
        file_size_formatted=format_file_size(row["file_size_bytes"]),
        upload_timestamp=ts or datetime.now(timezone.utc),
        processing_status=row.get("processing_status", "UPLOADED"),
        uploaded_by=row.get("uploaded_by", "admin"),
        table_name=row.get("table_name"),
        row_count=row.get("row_count"),
        column_count=row.get("column_count"),
        suggested_prompts=prompts,
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

    def get_dataset_by_table_name(self, table_name: str) -> Optional[DatasetMetadataSchema]:
        """
        Retrieves a dataset metadata record by its destination table name.
        """
        select_sql = """
        SELECT * FROM dataset_metadata
        WHERE table_name = %s
        ORDER BY upload_timestamp DESC
        LIMIT 1;
        """
        with database.get_readonly_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(select_sql, (table_name,))
                row = cursor.fetchone()

        return row_to_schema(row) if row else None

    def delete_dataset(self, dataset_id: str, drop_physical_table: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Safely deletes the dataset file from storage, removes the metadata record,
        and atomically drops the associated physical dynamic PostgreSQL table.

        Guarantees:
        - Resolves table_name solely from trusted dataset_metadata using dataset_id.
        - Refuses to drop any table in PROTECTED_SYSTEM_TABLES.
        - Validates table identifier format strictly (^([a-z_][a-z0-9_]{0,62})$).
        - Executes plain DROP TABLE IF EXISTS (no CASCADE) and metadata DELETE within a single transaction.
        - Deletes disk file only after successful database commit.

        Returns:
            Tuple[bool, Optional[str]]: (success, dropped_table_name)
        """
        dataset = self.get_dataset_by_id(dataset_id)
        if not dataset:
            return False, None

        table_to_drop = dataset.table_name

        # 1. Strict Protected Table Guardrail
        if table_to_drop and table_to_drop.lower() in PROTECTED_SYSTEM_TABLES:
            raise ValueError(f"Security Error: Cannot drop protected system table '{table_to_drop}'.")

        # 2. Strict Identifier Format Guardrail
        if table_to_drop and not re.match(r'^[a-z_][a-z0-9_]{0,62}$', table_to_drop):
            raise ValueError(f"Security Error: Invalid table identifier '{table_to_drop}'.")

        # 3. Transactional Database Deletion (Physical Table Drop + Metadata Record Delete)
        with database.get_admin_db_connection() as conn:
            with conn.cursor() as cursor:
                # Plain DROP TABLE IF EXISTS (without CASCADE)
                if drop_physical_table and table_to_drop:
                    drop_sql = sql.SQL("DROP TABLE IF EXISTS {}").format(
                        sql.Identifier(table_to_drop)
                    )
                    cursor.execute(drop_sql)

                # Delete metadata record
                delete_sql = "DELETE FROM dataset_metadata WHERE dataset_id = %s;"
                cursor.execute(delete_sql, (dataset_id,))
            conn.commit()

        # 4. Remove file from storage disk artifact (strictly post-commit)
        if dataset.stored_path:
            self.storage.delete_stored_file(dataset.stored_path)

        return True, table_to_drop

    def cleanup_orphan_dynamic_table(self, table_name: str) -> bool:
        """
        Targeted cleanup for a specific orphan dynamic table that is not registered in dataset_metadata.

        Strict Guardrails:
        1. Name cannot be in PROTECTED_SYSTEM_TABLES.
        2. Must be a valid PostgreSQL identifier matching ^[a-z_][a-z0-9_]{0,62}$.
        3. Must NOT be registered to an existing active dataset in dataset_metadata.
        4. Uses plain DROP TABLE IF EXISTS without CASCADE via admin connection.
        """
        clean_name = table_name.strip().lower()

        # Guardrail 1: Protected Table Block
        if clean_name in PROTECTED_SYSTEM_TABLES:
            raise ValueError(f"Security Error: Refusing to drop protected table '{clean_name}'.")

        # Guardrail 2: Identifier Format
        if not re.match(r'^[a-z_][a-z0-9_]{0,62}$', clean_name):
            raise ValueError(f"Security Error: Invalid table identifier format '{clean_name}'.")

        # Guardrail 3: Verify not currently registered to an active dataset
        existing_meta = self.get_dataset_by_table_name(clean_name)
        if existing_meta:
            raise ValueError(
                f"Table '{clean_name}' is actively registered to dataset ID '{existing_meta.dataset_id}'. "
                f"Use delete_dataset() instead."
            )

        # Execute targeted plain DROP TABLE
        with database.get_admin_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(clean_name)))
            conn.commit()

        return True

    def update_dataset_status(
        self,
        dataset_id: str,
        processing_status: str,
        table_name: Optional[str] = None,
        row_count: Optional[int] = None,
        column_count: Optional[int] = None,
        suggested_prompts: Optional[List[str]] = None,
        error_message: Optional[str] = None
    ) -> Optional[DatasetMetadataSchema]:
        """
        Updates dataset lifecycle processing status, table name, row count, prompts, and errors.
        """
        prompts_json = json.dumps(suggested_prompts) if suggested_prompts is not None else None
        update_sql = """
        UPDATE dataset_metadata
        SET processing_status = %s,
            table_name = COALESCE(%s, table_name),
            row_count = COALESCE(%s, row_count),
            column_count = COALESCE(%s, column_count),
            suggested_prompts = COALESCE(%s, suggested_prompts),
            error_message = %s
        WHERE dataset_id = %s
        RETURNING *;
        """
        with database.get_admin_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    update_sql,
                    (processing_status, table_name, row_count, column_count, prompts_json, error_message, dataset_id)
                )
                row = cursor.fetchone()
            conn.commit()

        return row_to_schema(row) if row else None

    def migrate_stored_paths_to_relative(self) -> int:
        """
        Safely normalizes legacy absolute filesystem paths in dataset_metadata
        into portable relative storage paths (e.g. 'data/uploads/<uuid>.<ext>').

        Guarantees:
        - Only converts paths that contain a valid dataset filename.
        - Skips records that are already stored as relative paths.
        - Preserves database integrity within a single transaction.
        - Does NOT delete or modify physical dataset files.

        Returns:
            int: Total count of records migrated.
        """
        rel_base = self.settings.upload_dir.replace("\\", "/").rstrip("/")
        updated_count = 0

        with database.get_admin_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT dataset_id, stored_path FROM dataset_metadata;")
                rows = cursor.fetchall()
                if not rows:
                    return 0

                for row in rows:
                    ds_id = row["dataset_id"]
                    current_path = row["stored_path"]
                    if not current_path:
                        continue

                    clean = current_path.replace("\\", "/").strip()

                    # If already a clean relative path starting with rel_base, skip
                    if clean.startswith(rel_base + "/"):
                        continue

                    # If it's a bare filename or legacy absolute path, extract filename
                    base_name = os.path.basename(clean)
                    if base_name and "." in base_name:
                        new_rel_path = f"{rel_base}/{base_name}"
                        cursor.execute(
                            "UPDATE dataset_metadata SET stored_path = %s WHERE dataset_id = %s;",
                            (new_rel_path, ds_id)
                        )
                        updated_count += 1

            conn.commit()

        logger.info(f"Migrated {updated_count} dataset_metadata stored_path records to relative format.")
        return updated_count
