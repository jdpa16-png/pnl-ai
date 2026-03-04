#!/usr/bin/env python3
"""
AI Expense Categorizer - Phase 1
Reads a bank CSV, categorizes automatically, and exports the result.
"""

import argparse
import sys
from pathlib import Path

from csv_reader import read_bank_csv
from classifier import ExpenseClassifier
from categories import CATEGORIES, ASSET_ACCOUNTS


def main():
    parser = argparse.ArgumentParser(description="AI Expense Categorizer")
    parser.add_argument("csv_file", help="Path to the bank-exported CSV")
    parser.add_argument(
        "--output", "-o", default="categorized_transactions.csv",
        help="Output file (default: categorized_transactions.csv)"
    )
    parser.add_argument(
        "--history", default="data/history.json",
        help="Path to previous categorizations history"
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="Automatic mode: never ask, always use best estimate"
    )
    args = parser.parse_args()

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
    export_results(results, output_path)

    # 4. Summary
    print(f"\n{'='*50}")
    print(f"✅ Results saved to: {output_path}")
    print_summary(results)


def export_results(results: list[dict], output_path: Path):
    """Exports results to CSV."""
    import csv

    fieldnames = [
        "Date", "Description", "Amount", "Currency",
        "Category", "Source_Account", "Confidence", "Type"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "Date": r.get("date", ""),
                "Description": r.get("description", ""),
                "Amount": r.get("amount", ""),
                "Currency": r.get("currency", "EUR"),
                "Category": r.get("category", "Uncategorized"),
                "Source_Account": r.get("source_account", "Actual"),
                "Confidence": r.get("confidence", ""),
                "Type": r.get("type", ""),
            })


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
