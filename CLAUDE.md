# AI Expense Categorizer — Project Rules

## What this project is
Python tool that reads CSV exports from banks (Revolut / Actual)
and automatically categorizes them using the Claude API. The user validates
uncertain entries interactively (CLI today, Telegram in the future).

## Current stack
- Python 3.11+ with strict type hints
- `anthropic` SDK for Claude API calls
- `python-dotenv` for environment variables
- No web frameworks — pure CLI in this phase

## File structure
```
pnl-ai/
├── main.py              # CLI entry point and final summary
├── classifier.py        # AI logic: history → keywords → Claude API → user
├── csv_reader.py        # Bank CSV parser (auto-detects delimiter)
├── categories.py        # Categories and keywords — user customizes here
├── requirements.txt
├── .env                 # API keys (never commit to git)
└── data/
    ├── history.json     # Memory of previous categorizations (auto-created)
    └── *.csv            # Bank CSV files
```

## Code conventions
- **Type hints** on all functions, no exceptions
- **Docstrings in English** for public classes and functions
- **snake_case** for variables and functions, **PascalCase** for classes
- Max ~150 lines per file — if it grows, extract a module
- f-strings for all string formatting (no `.format()` or `%`)
- Imports ordered: stdlib → third-party → local

## Architecture — how classification works
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
- Model to use is always `claude-sonnet-4-20250514`

## Required environment variables
```
ANTHROPIC_API_KEY=...          # Required now
GOOGLE_SHEETS_ID=...           # Phase 2
GOOGLE_CREDENTIALS_PATH=...    # Phase 2
REVOLUT_CLIENT_ID=...          # Phase 3
TELEGRAM_BOT_TOKEN=...         # Phase 4
TELEGRAM_CHAT_ID=...           # Phase 4
```

## Roadmap (implement in order)
1. ✅ **Phase 1** — CLI: CSV → categorize → export CSV
2. ⬜ **Phase 2** — `gsheets.py`: upload results to Google Sheets automatically
3. ⬜ **Phase 3** — `revolut.py`: fetch transactions in real time via API
4. ⬜ **Phase 4** — `telegram_bot.py`: validate uncertain entries via inline button messages
5. ⬜ **Phase 5** — Dashboard: expense visualization from Sheets

## Do NOT do this
- No hardcoded API keys in code — always from `.env`
- No Claude API calls if history or keywords already have the answer
- No saving to history for low or medium confidence categorizations
- No files over ~150 lines — extract modules
- No changing the model (`claude-sonnet-4-20250514`) without flagging it
- No auto-modifying `categories.py` — that's user territory

## Useful commands
```bash
# Test the full flow
python main.py data/example_transactions.csv

# Automatic mode without interactive prompts
python main.py data/transactions.csv --auto

# Run tests
pytest tests/ -v

# Inspect the history file
cat data/history.json | python -m json.tool
```

## When adding a new phase
1. Create the new module (e.g. `gsheets.py`) with isolated logic
2. Integrate it in `main.py` with an optional CLI flag (e.g. `--sheets`)
3. Add required environment variables to `.env.example`
4. Update this CLAUDE.md with the new commands and variables
