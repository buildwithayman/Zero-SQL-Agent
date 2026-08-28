"""
Unit and Integration Tests for Portable Dataset Storage Architecture
Verifies that stored_path is environment-independent, portable, and secure.
"""

import os
import shutil
import unittest
import uuid
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, UploadFile
import io

from backend.config import Settings
from backend.services.storage_service import StorageService
from backend.services.ingestion_service import IngestionService
from backend.services.dataset_service import DatasetService
from backend.schemas.dataset import DatasetMetadataSchema


class TestStoragePortability(unittest.TestCase):
    """Test suite verifying portable relative path resolution and containment security."""

    def setUp(self):
        self.test_upload_dir = "data/test_uploads_tmp"
        self.settings = Settings(
            environment="development",
            upload_dir=self.test_upload_dir
        )
        self.init_patcher = patch("backend.services.dataset_service.init_dataset_metadata_table")
        self.init_patcher.start()
        self.storage = StorageService(self.settings)

    def tearDown(self):
        self.init_patcher.stop()
        if os.path.exists(self.storage.upload_dir):
            shutil.rmtree(self.storage.upload_dir, ignore_errors=True)

    def test_relative_upload_dir_initialization(self):
        """Verify storage service initializes portable relative prefix and absolute directory."""
        self.assertEqual(self.storage.relative_upload_dir, "data/test_uploads_tmp")
        self.assertTrue(os.path.isabs(self.storage.upload_dir))
        self.assertTrue(os.path.exists(self.storage.upload_dir))

    def test_resolve_stored_path_modern_relative(self):
        """Verify modern relative path 'data/uploads/<uuid>.csv' resolves to absolute upload dir."""
        rel_path = f"{self.test_upload_dir}/test_file.csv"
        resolved = self.storage.resolve_stored_path(rel_path)
        expected = os.path.join(self.storage.upload_dir, "test_file.csv")
        self.assertEqual(resolved, os.path.abspath(expected))

    def test_resolve_stored_path_bare_filename(self):
        """Verify bare filename '<uuid>.csv' resolves inside upload dir."""
        bare_name = "test_file.csv"
        resolved = self.storage.resolve_stored_path(bare_name)
        expected = os.path.join(self.storage.upload_dir, "test_file.csv")
        self.assertEqual(resolved, os.path.abspath(expected))

    def test_resolve_stored_path_legacy_macos_absolute(self):
        """Verify legacy macOS absolute path resolves safely inside current host upload dir."""
        legacy_mac_path = "/Users/ayman/Desktop/SQL AI PRODUCT/data/uploads/sample_uuid.csv"
        resolved = self.storage.resolve_stored_path(legacy_mac_path)
        expected = os.path.join(self.storage.upload_dir, "sample_uuid.csv")
        self.assertEqual(resolved, os.path.abspath(expected))

    def test_resolve_stored_path_legacy_ec2_linux_absolute(self):
        """Verify legacy EC2 Linux absolute path resolves safely inside current host upload dir."""
        legacy_ec2_path = "/home/ec2-user/zero-sql/data/uploads/sample_uuid.csv"
        resolved = self.storage.resolve_stored_path(legacy_ec2_path)
        expected = os.path.join(self.storage.upload_dir, "sample_uuid.csv")
        self.assertEqual(resolved, os.path.abspath(expected))

    def test_resolve_stored_path_directory_traversal_blocked(self):
        """Verify directory traversal attempts are strictly caught and blocked."""
        traversal_attempts = [
            f"{self.test_upload_dir}/../../secret.txt",
            f"{self.test_upload_dir}/../../../etc/passwd",
        ]
        for bad_path in traversal_attempts:
            with self.assertRaises(HTTPException) as ctx:
                self.storage.resolve_stored_path(bad_path)
            self.assertEqual(ctx.exception.status_code, 400)
            self.assertIn("traversal", ctx.exception.detail.lower())

    def test_save_raw_bytes_returns_relative_path_and_writes_physically(self):
        """Verify save_raw_bytes persists to disk and returns portable relative path."""
        content = b"col1,col2\n10,20\n"
        ds_id, orig_name, stored_path, size, ext = self.storage.save_raw_bytes(
            content=content,
            original_filename="metrics.csv",
            file_format="csv"
        )
        # Stored path MUST be relative
        self.assertFalse(os.path.isabs(stored_path))
        self.assertTrue(stored_path.startswith(f"{self.test_upload_dir}/"))
        self.assertTrue(stored_path.endswith(f"{ds_id}.csv"))

        # Physical file MUST exist on disk at resolved absolute path
        abs_path = self.storage.resolve_stored_path(stored_path)
        self.assertTrue(os.path.exists(abs_path))
        with open(abs_path, "rb") as f:
            self.assertEqual(f.read(), content)

        # Deletion works with relative path
        self.assertTrue(self.storage.delete_stored_file(stored_path))
        self.assertFalse(os.path.exists(abs_path))

    def test_ingestion_service_resolves_and_verifies_relative_path(self):
        """Verify IngestionService._get_verified_dataset_meta works with relative stored_path."""
        from datetime import datetime, timezone
        content = b"col1,col2\n10,20\n"
        ds_id, orig_name, stored_path, size, ext = self.storage.save_raw_bytes(
            content=content,
            original_filename="test.csv",
            file_format="csv"
        )
        fake_meta = DatasetMetadataSchema(
            dataset_id=ds_id,
            dataset_name="Test Dataset",
            original_filename=orig_name,
            stored_path=stored_path,
            file_format="csv",
            file_size_bytes=size,
            file_size_formatted="20 B",
            upload_timestamp=datetime.now(timezone.utc)
        )

        ingestion_svc = IngestionService(self.settings)
        with patch.object(ingestion_svc.dataset_svc, "get_dataset_by_id", return_value=fake_meta):
            dataset, abs_path = ingestion_svc._get_verified_dataset_meta(ds_id)
            self.assertEqual(dataset.dataset_id, ds_id)
            self.assertTrue(os.path.isabs(abs_path))
            self.assertTrue(os.path.exists(abs_path))

    def test_migrate_stored_paths_to_relative(self):
        """Verify migrate_stored_paths_to_relative converts absolute paths and skips relatives."""
        mock_rows = [
            {"dataset_id": "1", "stored_path": "/Users/ayman/Desktop/SQL AI PRODUCT/data/uploads/file1.csv"},
            {"dataset_id": "2", "stored_path": "data/test_uploads_tmp/file2.csv"},
            {"dataset_id": "3", "stored_path": "/home/ec2-user/zero-sql/data/uploads/file3.csv"},
            {"dataset_id": "4", "stored_path": "file4.csv"},
        ]
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_rows
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_conn

        dataset_svc = DatasetService(self.settings)
        with patch("database.get_admin_db_connection", return_value=mock_ctx):
            count = dataset_svc.migrate_stored_paths_to_relative()
            # Records 1, 3, and 4 need normalization; record 2 is already relative to 'data/test_uploads_tmp/'
            self.assertEqual(count, 3)
            self.assertEqual(mock_cursor.execute.call_count, 4)  # 1 SELECT + 3 UPDATEs


if __name__ == "__main__":
    unittest.main(verbosity=2)

