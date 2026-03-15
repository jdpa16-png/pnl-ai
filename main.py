#!/usr/bin/env python3
"""
AI Expense Categorizer - Phase 1
Reads a bank CSV, categorizes automatically, and exports the result.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from csv_reader import read_bank_csv
from classifier import ExpenseClassifier
from categories import ACCOUNTS_PLAN, COSTS_PLAN

SHEET_NAME_DISPLAY = "DIARIO AUTO"

def main():
    parser = argparse.ArgumentParser(description="AI Expense Categorizer")
    parser.add_argument("csv_file", help="Path to the bank-exported CSV")
    parser.add_argument(
        "--output", "-o", default="data/categorized_transactions.csv",
        help="Output file (default: data/categorized_transactions.csv)"
    )
    parser.add_argument(
        "--history", default="data/history.json",
        help="Path to previous categorizations history"
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="Automatic mode: never ask, always use best estimate"
    )
    parser.add_argument(
        "--account", "-a",
        help="Asset account code for this CSV (e.g. 211 for 'Cuenta principal Jaime')"
    )
    parser.add_argument(
        "--sheets", action="store_true",
        help="Upload results to Google Sheets (DIARIO AUTO)"
    )
    args = parser.parse_args()

    if args.account and args.account not in ACCOUNTS_PLAN:
        print(f"⚠️  Warning: account code '{args.account}' not found in ACCOUNTS_PLAN")
        print("   Available codes:", ", ".join(k for k in ACCOUNTS_PLAN if len(k) == 3))

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"❌ Error: File not found: {csv_path}")
        sys.exit(1)

    print(f"\n💰 AI Expense Categorizer")
    print(f"{'='*50}")
    print(f"📂 Reading: {csv_path.name}")

    # 1. Read CSV
    transactions = read_bank_csv(csv_path)
    print(f"✅ {len(transactions)} transactions loaded\n")

    # 2. Classify
    classifier = ExpenseClassifier(
        history_path=args.history,
        interactive=not args.auto
    )

    results = classifier.classify_batch(transactions)

    # 3. Export
    output_path = Path(args.output)
    export_results(results, output_path, account_code=args.account)

    # 4. Upload to Sheets (optional)
    if args.sheets:
        print("\n📤 Uploading to Google Sheets...")
        try:
            from gsheets import upload_to_sheets
            rows_added = upload_to_sheets(results, account_code=args.account)
            print(f"✅ {rows_added} rows appended to '{SHEET_NAME_DISPLAY}'")
        except Exception as e:
            print(f"❌ Google Sheets upload failed: {e}")

    # 5. Summary
    print(f"\n{'='*50}")
    print(f"✅ Results saved to: {output_path}")
    print_summary(results)


def export_results(results: list[dict], output_path: Path, account_code: str | None = None):
    """
    Exports results to CSV using double-entry bookkeeping: 2 rows per transaction.

    For expenses (amount < 0):
      Row 1 (FROM asset):    asset_code, asset_description, date, desc, -abs(amount)
      Row 2 (TO category):   category,   category,          date, desc, +abs(amount)

    For income (amount > 0):
      Row 1 (FROM category): category,   category,          date, desc, -amount
      Row 2 (TO asset):      asset_code, asset_description, date, desc, +amount
    """
    import csv

    asset_code = account_code or "???"
    asset_description = ACCOUNTS_PLAN.get(asset_code, asset_code)

    fieldnames = ["code", "description", "date", "movement_description", "amount"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            amount: float = r.get("amount", 0.0)
            date: str = r.get("date", "")
            desc: str = r.get("description", "")
            category: str = r.get("category", "Uncategorized")
            abs_amount = abs(amount)

            category_desc = COSTS_PLAN.get(category, category)

            if amount < 0:
                # Expense: money leaves asset → goes to cost category
                writer.writerow({"code": asset_code, "description": asset_description,
                                 "date": date, "movement_description": desc, "amount": -abs_amount})
                writer.writerow({"code": category, "description": category_desc,
                                 "date": date, "movement_description": desc, "amount": abs_amount})
            else:
                # Income: money comes from income category → enters asset
                writer.writerow({"code": category, "description": category_desc,
                                 "date": date, "movement_description": desc, "amount": -amount})
                writer.writerow({"code": asset_code, "description": asset_description,
                                 "date": date, "movement_description": desc, "amount": amount})


def print_summary(results: list[dict]):
    """Prints expense summary by category."""
    from collections import defaultdict

    by_category = defaultdict(float)
    for r in results:
        if r.get("amount", 0) < 0:  # Expenses only
            cat = r.get("category", "Uncategorized")
            by_category[cat] += abs(r["amount"])

    print("\n📊 Expense summary:")
    for cat, total in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat:<30} {total:>8.2f} EUR")

    total_expenses = sum(v for v in by_category.values())
    total_income = sum(r["amount"] for r in results if r.get("amount", 0) > 0)
    print(f"\n  {'Total expenses':<30} {total_expenses:>8.2f} EUR")
    print(f"  {'Total income':<30} {total_income:>8.2f} EUR")
    print(f"  {'Balance':<30} {total_income - total_expenses:>8.2f} EUR")


if __name__ == "__main__":
    main()
