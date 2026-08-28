#!/usr/bin/env python3
"""
ZeroSQL AI V2 — Dataset Stored Path Portability Migration Script
Normalizes legacy absolute filesystem paths in dataset_metadata to portable relative paths.

Usage:
    python scripts/migrate_stored_paths.py
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import get_settings
from backend.services.dataset_service import DatasetService


def main():
    print("=" * 70)
    print("  ZeroSQL AI V2 — Stored Path Portability Migration")
    print("=" * 70)

    settings = get_settings()
    dataset_svc = DatasetService(settings)

    print(f"[*] Target Relative Base: '{dataset_svc.settings.upload_dir}'")
    print("[*] Normalizing legacy absolute paths in dataset_metadata...")

    count = dataset_svc.migrate_stored_paths_to_relative()

    print(f"[+] Successfully migrated {count} records to portable relative format.")
    print("=" * 70)


if __name__ == "__main__":
    main()
