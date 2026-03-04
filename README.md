# 💰 AI Expense Categorizer

Python CLI tool that reads bank CSV exports and automatically categorizes them using Claude AI.

## Quick setup

```bash
# 1. Clone / unzip the project
cd pnl-ai

# 2. Create virtual environment
python3 -m venv env
source env/bin/activate  # Windows: env\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY
# (get one at https://console.anthropic.com)
```

## Usage

```bash
# Interactive mode (asks when uncertain)
python main.py data/example_transactions.csv

# Automatic mode (no prompts, uses best estimate)
python main.py data/transactions.csv --auto

# Specify output file
python main.py data/january.csv -o january_results.csv
```

## How it works

```
Bank CSV → Read → Categorize → Export CSV ready for Google Sheets
                      │
                      ├── 1. Check history (no API)
                      ├── 2. Obvious keywords (no API)
                      ├── 3. Claude AI
                      └── 4. Ask user if uncertain
```

History is saved to `data/history.json`. Over time, the system learns your patterns and needs fewer API calls.

## Customization

Edit `categories.py` to:
- Adjust your expense/income categories
- Add your bank accounts
- Add keywords for fast classification

## Roadmap

- [x] **Phase 1** — Local CLI: CSV → categorization → export
- [ ] **Phase 2** — Google Sheets: upload results automatically
- [ ] **Phase 3** — Revolut API: fetch transactions in real time
- [ ] **Phase 4** — Telegram Bot: validate uncertain entries via message
- [ ] **Phase 5** — Dashboard: expense visualization

## Structure

```
pnl-ai/
├── main.py           # CLI entry point
├── classifier.py     # Categorization logic with Claude
├── csv_reader.py     # Bank CSV parser
├── categories.py     # Your categories (customize here)
├── requirements.txt
├── .env.example      # Environment variables template
└── data/
    ├── example_transactions.csv   # Sample CSV
    └── history.json               # Auto-created
```
