"""
Dataset Storage and Validation Service
Manages file validation, sanitization, disk persistence, and deletion.
"""

import os
import re
import json
import uuid
import io
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from backend.config import Settings


def format_file_size(size_bytes: int) -> str:
    """Formats raw byte count into human readable units (B, KB, MB, GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes raw uploaded filename to prevent directory traversal and injection attacks.
    Preserves valid characters while stripping path delimiters and malicious patterns.
    """
    if not filename:
        return "unnamed_dataset"
    # Strip any directory path components (both unix / and windows \)
    base = os.path.basename(filename.replace("\\", "/"))
    # Remove null bytes and special shell control characters
    cleaned = re.sub(r'[\x00-\x1f\x7f<>:"/\\|?*]', '', base).strip()
    return cleaned if cleaned else "unnamed_dataset"


def extract_file_extension(filename: str) -> str:
    """Extracts and normalizes the lowercase extension without leading dot."""
    parts = filename.rsplit(".", 1)
    if len(parts) > 1:
        return parts[1].lower().strip()
    return ""


def validate_file_content(file_bytes: bytes, file_format: str) -> Tuple[bool, str]:
    """
    Performs deep content and structural validation on uploaded dataset bytes.
    Ensures file is non-empty, matches claimed format, and is structurally readable.
    """
    if len(file_bytes) == 0:
        return False, "Validation Error: Uploaded file is empty (0 bytes)."

    fmt = file_format.lower()

    if fmt == "csv":
        try:
            # Try utf-8 decoding
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = file_bytes.decode("latin-1")
            except Exception as e:
                return False, f"Validation Error: CSV file cannot be decoded as text ({str(e)})."

        # Verify at least one non-empty line
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return False, "Validation Error: CSV contains no valid data rows."
        return True, "Valid CSV format."

    elif fmt == "json":
        try:
            text = file_bytes.decode("utf-8")
            data = json.loads(text)
            if not isinstance(data, (list, dict)):
                return False, "Validation Error: JSON dataset must be a list of records or a valid data dictionary."
            if isinstance(data, list) and len(data) == 0:
                return False, "Validation Error: JSON array contains 0 records."
            return True, "Valid JSON format."
        except Exception as e:
            return False, f"Validation Error: Malformed JSON dataset ({str(e)})."

    elif fmt in ("xlsx", "excel"):
        # Excel .xlsx is a ZIP container starting with PK (0x50, 0x4B)
        if not file_bytes.startswith(b"PK\x03\x04"):
            return False, "Validation Error: File does not appear to be a valid XLSX spreadsheet (magic bytes mismatch)."
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True)
            if not wb.sheetnames:
                return False, "Validation Error: Excel file contains no worksheets."
            return True, "Valid XLSX format."
        except Exception as e:
            return False, f"Validation Error: Unable to read Excel workbook ({str(e)})."

    elif fmt == "parquet":
        # Parquet files must start and end with magic bytes 'PAR1'
        if len(file_bytes) < 8 or not (file_bytes.startswith(b"PAR1") and file_bytes.endswith(b"PAR1")):
            return False, "Validation Error: File does not contain valid Parquet header/footer magic bytes (PAR1)."
        try:
            import pyarrow.parquet as pq
            reader = pq.ParquetFile(io.BytesIO(file_bytes))
            if reader.metadata.num_rows == 0 and reader.metadata.num_columns == 0:
                return False, "Validation Error: Parquet file has 0 rows and columns."
            return True, "Valid Parquet format."
        except Exception as e:
            return False, f"Validation Error: Unable to read Parquet dataset ({str(e)})."

    else:
        return False, f"Validation Error: Unsupported file format '{fmt}'. Supported formats are CSV, XLSX, JSON, Parquet."


class StorageService:
    """Handles secure file persistence and deletion."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.upload_dir = os.path.abspath(settings.upload_dir)
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save_uploaded_file(
        self,
        upload_file: UploadFile
    ) -> Tuple[str, str, str, int, str]:
        """
        Validates, sanitizes, and persists an uploaded file.
        
        Returns:
            Tuple[dataset_id, original_filename, stored_path, file_size_bytes, file_format]
        """
        raw_filename = upload_file.filename or "dataset"
        original_filename = sanitize_filename(raw_filename)
        ext = extract_file_extension(original_filename)

        # 1. Validate Extension
        if ext not in self.settings.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format '{ext}'. Allowed formats: {', '.join(self.settings.allowed_extensions).upper()}"
            )

        # 2. Read bytes with size protection
        content = await upload_file.read()
        file_size = len(content)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)."
            )

        if file_size > self.settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({format_file_size(file_size)}) exceeds maximum limit of {self.settings.max_upload_size_mb} MB."
            )

        # 3. Deep Content Validation
        is_valid, reason = validate_file_content(content, ext)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=reason
            )

        # 4. Generate Safe Unique Filename on Disk
        dataset_id = str(uuid.uuid4())
        stored_filename = f"{dataset_id}.{ext}"
        stored_path = os.path.join(self.upload_dir, stored_filename)

        # Guarantee no path traversal outside upload_dir
        if not os.path.abspath(stored_path).startswith(self.upload_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security Error: Path traversal attempt detected."
            )

        # Write to disk
        try:
            with open(stored_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to persist dataset to storage: {str(e)}"
            )

        return dataset_id, original_filename, stored_path, file_size, ext

    def save_raw_bytes(
        self,
        content: bytes,
        original_filename: str,
        file_format: Optional[str] = None
    ) -> Tuple[str, str, str, int, str]:
        """
        Validates, sanitizes, and persists raw bytes (e.g. from catalog download).
        Enforces size limit, content structure validation, and UUID storage.
        
        Returns:
            Tuple[dataset_id, original_filename, stored_path, file_size_bytes, file_format]
        """
        safe_orig_name = sanitize_filename(original_filename)
        ext = file_format.lower().strip() if file_format else extract_file_extension(safe_orig_name)
        if not ext:
            ext = "csv"

        # 1. Validate Extension
        if ext not in self.settings.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format '{ext}'. Allowed formats: {', '.join(self.settings.allowed_extensions).upper()}"
            )

        # 2. Check Size
        file_size = len(content)
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset content is empty (0 bytes)."
            )

        if file_size > self.settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Dataset size ({format_file_size(file_size)}) exceeds maximum limit of {self.settings.max_upload_size_mb} MB."
            )

        # 3. Deep Content Validation
        is_valid, reason = validate_file_content(content, ext)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=reason
            )

        # 4. Generate Safe Unique Filename on Disk
        dataset_id = str(uuid.uuid4())
        stored_filename = f"{dataset_id}.{ext}"
        stored_path = os.path.join(self.upload_dir, stored_filename)

        if not os.path.abspath(stored_path).startswith(self.upload_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security Error: Path traversal attempt detected."
            )

        try:
            with open(stored_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to persist dataset to storage: {str(e)}"
            )

        return dataset_id, safe_orig_name, stored_path, file_size, ext


    def delete_stored_file(self, stored_path: str) -> bool:
        """
        Safely deletes the stored file from disk if it exists.
        Guards against arbitrary path deletion outside upload_dir.
        """
        if not stored_path:
            return False
        abs_path = os.path.abspath(stored_path)
        if not abs_path.startswith(self.upload_dir):
            # Guard against deleting files outside upload_dir
            return False
        if os.path.exists(abs_path) and os.path.isfile(abs_path):
            try:
                os.remove(abs_path)
                return True
            except Exception:
                return False
        return False
