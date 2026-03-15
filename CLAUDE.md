# PnL AI — Project Rules

## What this project is
Personal finance app that categorizes bank transactions using the Claude API.
Started as a CLI tool; now a full web app with React frontend, FastAPI backend,
Google Sheets export, and planned live Revolut integration.

## Current stack
- **Backend**: Python 3.11+, FastAPI, WebSockets, uvicorn[standard]
- **Frontend**: React 18 + Vite + TypeScript, Tailwind CSS v4, Recharts, React Router
- **AI**: `anthropic` SDK — model `claude-sonnet-4-20250514`
- **Sheets**: `gspread` + Google service account
- **Config**: `python-dotenv`

## Actual file structure
```
pnl-ai/
├── backend/
│   ├── __init__.py
│   ├── api.py           # FastAPI app: all REST routes + WebSocket endpoint
│   └── ws_manager.py    # Per-session WebSocket registry + async/sync bridge
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Upload.tsx     # Page 1: CSV drop, account selector, live log, question cards
│   │   │   ├── Dashboard.tsx  # Page 2: charts, table, inline category editing, Sheets upload
│   │   │   └── History.tsx    # Page 3: view/edit/delete history.json entries
│   │   ├── accounts.ts        # ACCOUNT_OPTIONS list + SHEETS_URL constant
│   │   ├── types.ts           # Shared TS types (Transaction, WsMessage, etc.)
│   │   └── App.tsx            # React Router (/, /dashboard, /history)
│   ├── vite.config.ts         # Tailwind plugin + /api proxy to :8000
│   └── package.json
├── main.py              # CLI entry point — still fully functional
├── classifier.py        # Core: history → keywords → Claude → ask (ask_fn + on_progress callbacks)
├── csv_reader.py        # Bank CSV parser, auto-detects delimiter + column names (ES/EN)
├── categories.py        # COSTS_PLAN, ACCOUNTS_PLAN, KEYWORD_HINTS — USER TERRITORY
├── gsheets.py           # Google Sheets uploader (double-entry rows → DIARIO AUTO)
├── requirements.txt
├── .env                 # Never commit
├── docs/
│   └── architecture.md
└── data/
    ├── history.json         # Auto-created learned classifications
    ├── credentials.json     # Google service account — never commit
    └── *.csv
```

## Code conventions
- **Type hints** on all functions, no exceptions
- **Docstrings in English** for public classes and functions
- **snake_case** for variables and functions, **PascalCase** for classes
- Max ~150 lines per file — extract modules when growing
- f-strings for all string formatting
- Imports ordered: stdlib → third-party → local

## Required environment variables
```
ANTHROPIC_API_KEY=...          # Required — Claude API
GOOGLE_SHEETS_ID=...           # Phase 2 — spreadsheet ID
GOOGLE_CREDENTIALS_PATH=...    # Phase 2 — service account JSON path
REVOLUT_WEBHOOK_SECRET=...     # Phase 4 — webhook HMAC secret
REVOLUT_API_KEY=...            # Phase 4 — Revolut Business API key
```

## Roadmap
1. ✅ **Phase 1** — CLI: CSV → classify → export CSV
2. ✅ **Phase 2** — `gsheets.py`: double-entry upload to Google Sheets
3. ✅ **Phase 3** — Web App (FastAPI + React):
   - Upload page: CSV drag & drop, account selector, live terminal log
   - Interactive classification via WebSocket (question cards replace CLI prompts)
   - Dashboard: bar chart, category table, summary cards, inline category editing
   - History page: view, edit, delete `history.json` entries
4. ⬜ **Phase 4** — Live Revolut:
   - `backend/revolut.py`: receive HMAC-verified webhooks
   - Classify in real time using same pipeline
   - Push new transactions to all connected browsers via WebSocket
   - Auto-append to Google Sheets

## Do NOT do this
- No hardcoded API keys — always from `.env`
- No Claude API calls if history or keywords already answer the question
- No saving to history for low or medium confidence (only `high`)
- No files over ~150 lines — extract modules
- No changing the model (`claude-sonnet-4-20250514`) without flagging it
- No auto-modifying `categories.py` — that's user territory
- No Streamlit — can't handle Revolut webhooks or real WebSockets

## Useful commands
```bash
# ── Backend ───────────────────────────────────────────────────────────────────
source .pnlai/bin/activate
uvicorn backend.api:app --reload --port 8000

# ── Frontend ──────────────────────────────────────────────────────────────────
cd frontend && npm run dev       # http://localhost:5173

# ── CLI (still works) ─────────────────────────────────────────────────────────
python main.py data/gastos-marzo.csv --account 211
python main.py data/gastos-marzo.csv --account 211 --sheets --auto

# ── Install ───────────────────────────────────────────────────────────────────
pip install -r requirements.txt
cd frontend && npm install
```

## Key design decisions
- **WebSocket async/sync bridge**: `classifier.py` runs in a thread (`asyncio.to_thread`).
  When uncertain, `sync_ask()` in `api.py` calls `run_coroutine_threadsafe()` to push
  the question to the browser and block the thread until an answer arrives via the WS.
- **CLI stays sync**: `classifier.py` uses `ask_fn` callback — `None` → uses `input()`,
  provided → bridges to WebSocket. CLI needs no changes.
- **History is only written for `confidence == "high"`** to avoid learning from mistakes.

## When adding Phase 4
1. Create `backend/revolut.py` with webhook receiver (HMAC verify → parse → classify)
2. Add `POST /webhook/revolut` route in `api.py`
3. Reuse `ws_manager` to push live transactions to all connected clients
4. Add a live feed section to `Dashboard.tsx`
5. Add `REVOLUT_WEBHOOK_SECRET` and `REVOLUT_API_KEY` to `.env`
6. Update this file and `docs/architecture.md`
