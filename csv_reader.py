"""
Bank CSV export parser.
Supports the Revolut/Actual format with columns:
Type, Product, Started Date, Completed Date,
Description, Amount, Fee, Currency, State, Balance
"""
from __future__ import annotations

import csv
from pathlib import Path
from datetime import datetime


def read_bank_csv(filepath: Path) -> list[dict]:
    """
    Reads the bank CSV and returns a list of normalized transactions.

    Returns:
        List of dicts with keys: date, description, amount,
        currency, type, balance, state
    """
    transactions = []

    # Auto-detect delimiter
    with open(filepath, "r", encoding="utf-8-sig") as f:
        sample = f.read(2048)

    delimiter = ";" if sample.count(";") > sample.count(",") else ","

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delimiter)

        for i, row in enumerate(reader):
            try:
                tx = parse_row(row, i)
                if tx:
                    transactions.append(tx)
            except Exception as e:
                print(f"⚠️  Row {i+2} skipped: {e} — {dict(row)}")

    # Sort by date descending (most recent first)
    transactions.sort(key=lambda x: x["date"], reverse=True)
    return transactions


def parse_row(row: dict, index: int) -> dict | None:
    """Parses a CSV row and returns a normalized dict."""

    # Normalize column names (strip spaces, lowercase)
    row = {k.strip(): v.strip() if isinstance(v, str) else v for k, v in row.items()}

    # Description
    description = (
        row.get("Descripción") or
        row.get("Descripcion") or
        row.get("Description") or
        row.get("Concepto") or
        ""
    ).strip()

    if not description:
        return None  # Empty rows or duplicate headers

    # Amount
    amount_raw = (
        row.get("Importe") or
        row.get("Amount") or
        row.get("Monto") or
        "0"
    )
    try:
        amount = float(str(amount_raw).replace(",", ".").replace(" ", ""))
    except ValueError:
        print(f"⚠️  Invalid amount: '{amount_raw}' for '{description}'")
        amount = 0.0

    # Date
    date_raw = (
        row.get("Fecha de inicio") or
        row.get("Fecha") or
        row.get("Date") or
        row.get("Started Date") or
        ""
    )
    date = parse_date(date_raw)

    # Currency
    currency = row.get("Divisa") or row.get("Currency") or "EUR"

    # Operation type
    tx_type = row.get("Tipo") or row.get("Type") or ""

    # State
    state = row.get("State") or row.get("Status") or "COMPLETED"

    # Skip reverted/declined/failed transactions
    if state.upper() in ("REVERTED", "DECLINED", "FAILED"):
        return None

    return {
        "id": index,
        "date": date,
        "description": description,
        "amount": amount,
        "currency": currency,
        "type": tx_type,
        "state": state,
        "balance": float(str(row.get("Saldo", "0") or row.get("Balance", "0")).replace(",", ".") or 0),
    }


def parse_date(date_raw: str) -> str:
    """Parses a date in various formats, returns YYYY-MM-DD."""
    if not date_raw:
        return ""

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_raw.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # If no format matches, return as-is
    return date_raw.strip()
