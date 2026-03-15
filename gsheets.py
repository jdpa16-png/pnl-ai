"""
Phase 2 — Google Sheets uploader.
Appends double-entry rows to the 'DIARIO AUTO' sheet.
"""

from __future__ import annotations

import os
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from categories import ACCOUNTS_PLAN, COSTS_PLAN

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "DIARIO AUTO"


def _get_client() -> gspread.Client:
    """Authenticates using the service account credentials file."""
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "")
    if not creds_path or not Path(creds_path).exists():
        raise FileNotFoundError(
            f"GOOGLE_CREDENTIALS_PATH not set or file not found: '{creds_path}'\n"
            "Create a service account, download the JSON key, and set the path in .env"
        )
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(creds)


def upload_to_sheets(results: list[dict], account_code: str | None = None) -> int:
    """
    Appends double-entry rows to the DIARIO AUTO sheet.

    Returns the number of rows appended.
    """
    sheets_id = os.environ.get("GOOGLE_SHEETS_ID", "")
    if not sheets_id:
        raise ValueError("GOOGLE_SHEETS_ID not set in .env")

    client = _get_client()
    spreadsheet = client.open_by_key(sheets_id)
    available = [ws.title for ws in spreadsheet.worksheets()]
    if SHEET_NAME not in available:
        raise ValueError(
            f"Sheet '{SHEET_NAME}' not found. Available sheets: {available}"
        )
    worksheet = spreadsheet.worksheet(SHEET_NAME)

    asset_code = account_code or "???"
    asset_description = ACCOUNTS_PLAN.get(asset_code, asset_code)

    rows: list[list] = []
    for r in results:
        amount: float = r.get("amount", 0.0)
        date: str = r.get("date", "")
        desc: str = r.get("description", "")
        category: str = r.get("category", "Uncategorized")
        abs_amount = abs(amount)
        category_desc = COSTS_PLAN.get(category, category)

        # Per-entry account overrides the batch-level default
        row_asset_code = r.get("account_code") or asset_code
        row_asset_desc = ACCOUNTS_PLAN.get(row_asset_code, row_asset_code)

        if amount < 0:
            rows.append([row_asset_code, row_asset_desc, date, desc, -abs_amount])
            rows.append([category, category_desc, date, desc, abs_amount])
        else:
            rows.append([category, category_desc, date, desc, -amount])
            rows.append([row_asset_code, row_asset_desc, date, desc, amount])

    if rows:
        worksheet.append_rows(rows, value_input_option="USER_ENTERED")

    return len(rows)
