# Architecture

## Classification pipeline

```
CSV → csv_reader.py → list of transactions (dicts)
                              ↓
                      classifier.py
                        1. exact history match  (no API)
                        2. keyword match        (no API)
                        3. Claude API           (with API)
                        4. ask user             (if low confidence)
                              ↓
                      main.py → export CSV + summary
```

- `history.json` is the persistent memory across runs
- Only saved to history if `confidence == "high"`
- Model: `claude-sonnet-4-20250514`

## Module responsibilities

| File | Role |
|------|------|
| `main.py` | CLI entry point, export, summary |
| `classifier.py` | `ExpenseClassifier` — all classification logic |
| `csv_reader.py` | Bank CSV parser, auto-detects `,` vs `;` delimiter |
| `categories.py` | `COSTS_PLAN`, `ACCOUNTS_PLAN`, `KEYWORD_HINTS` — user-owned |

## Export format — double-entry bookkeeping

The output CSV uses double-entry accounting: **2 rows per transaction**.

Output columns: `code`, `description`, `date`, `movement_description`, `amount`

For **expenses** (amount < 0):
- Row 1 (FROM asset): `asset_code`, asset name, date, desc, `-abs(amount)`
- Row 2 (TO cost):    category code, category name, date, desc, `+abs(amount)`

For **income** (amount > 0):
- Row 1 (FROM income): category code, category name, date, desc, `-amount`
- Row 2 (TO asset):    `asset_code`, asset name, date, desc, `+amount`

Asset codes come from `ACCOUNTS_PLAN` in `categories.py` (3-digit leaf codes, e.g. `211` = "Cuenta principal Jaime"). Pass the correct one via `--account`.

## categories.py structure

```
ACCOUNTS_PLAN  — hierarchical chart of asset accounts (Grupo 2)
  1-digit key  → group header (e.g. "2" = "ACTIVO")
  2-digit key  → sub-group   (e.g. "21" = "CUENTAS SANTANDER")
  3-digit key  → leaf node   (e.g. "211" = "Cuenta principal Jaime")

ASSET_ACCOUNTS — list of leaf account names (auto-derived from ACCOUNTS_PLAN)

COSTS_PLAN     — hierarchical chart of expense/income codes (Grupos 4–9 + alphanumeric income)
  1-digit key  → group header
  2-digit key  → sub-group
  3+ digit key → leaf node (expense)
  alpha key    → income leaf (e.g. "SU-J" = "Sueldo Jaime")

CATEGORIES     — list of leaf codes only (what the AI classifies into)
KEYWORD_HINTS  — dict[lowercase_keyword → leaf_code] for fast pre-classification
```

## CLI flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--output` | `-o` | `categorized_transactions.csv` | Output CSV path |
| `--history` | | `data/history.json` | Path to history file |
| `--auto` | | `false` | Never ask user, always use best estimate |
| `--account` | `-a` | `???` | 3-digit asset account code from `ACCOUNTS_PLAN` |
