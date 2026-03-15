"""
Staging file management for categorized_transactions.csv.
Acts as an accumulator for classified transactions not yet uploaded to Sheets.
After a successful upload, the file is cleared to avoid double-counting.
"""
from __future__ import annotations

import csv
from pathlib import Path

STAGING_PATH = Path(__file__).parent.parent / "data" / "categorized_transactions.csv"
FIELDNAMES = ["date", "description", "amount", "category", "account_code", "confidence", "method"]


def _key(r: dict) -> tuple:
    """Deduplication key: (date, description, rounded_amount)."""
    try:
        amt = round(float(r.get("amount", 0)), 2)
    except (ValueError, TypeError):
        amt = 0.0
    return (r.get("date", ""), r.get("description", ""), amt)


def _load_existing() -> list[dict]:
    if not STAGING_PATH.exists():
        return []
    with STAGING_PATH.open(encoding="utf-8", newline="") as f:
        first = f.readline().strip()
        if not first:
            return []
        f.seek(0)
        if first.startswith("date,"):
            return list(csv.DictReader(f))
        else:
            # Headerless legacy file — parse with explicit fieldnames
            return list(csv.DictReader(f, fieldnames=FIELDNAMES))


def _rewrite_with_header(rows: list[dict]) -> None:
    """Rewrite the staging file with a proper header row."""
    STAGING_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STAGING_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _ensure_header() -> None:
    """Add a header row to the file if it is missing (one-time migration)."""
    if not STAGING_PATH.exists():
        return
    with STAGING_PATH.open(encoding="utf-8") as f:
        first = f.readline().strip()
    if not first.startswith("date,"):
        rows = _load_existing()
        _rewrite_with_header(rows)


def load_all() -> list[dict]:
    """Returns all staged rows with amounts parsed to float."""
    _ensure_header()
    result = []
    for r in _load_existing():
        try:
            amount = float(r.get("amount", 0) or 0)
        except (ValueError, TypeError):
            amount = 0.0
        result.append({
            "date": r.get("date", ""),
            "description": r.get("description", ""),
            "amount": amount,
            "category": r.get("category", ""),
            "account_code": r.get("account_code", ""),
            "confidence": r.get("confidence", ""),
            "method": r.get("method", ""),
        })
    return result


def append_results(new_results: list[dict]) -> list[dict]:
    """
    Appends non-duplicate results to the staging file.
    Returns the list of detected duplicates (already present in staging).
    """
    _ensure_header()
    existing = _load_existing()
    existing_keys = {_key(r) for r in existing}

    duplicates: list[dict] = []
    to_add: list[dict] = []
    for r in new_results:
        if _key(r) in existing_keys:
            duplicates.append(r)
        else:
            to_add.append(r)

    if to_add:
        STAGING_PATH.parent.mkdir(parents=True, exist_ok=True)
        write_header = not STAGING_PATH.exists()
        with STAGING_PATH.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
            if write_header:
                writer.writeheader()
            for r in to_add:
                writer.writerow({
                    "date": r.get("date", ""),
                    "description": r.get("description", ""),
                    "amount": r.get("amount", 0),
                    "category": r.get("category", ""),
                    "account_code": r.get("account_code", ""),
                    "confidence": r.get("confidence", ""),
                    "method": r.get("source", r.get("method", "")),
                })

    return duplicates


def clear() -> None:
    """Resets the staging file to header-only (called after a successful Sheets upload)."""
    STAGING_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STAGING_PATH.open("w", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()
