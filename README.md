# 💰 PnL AI

Personal finance app that reads bank CSV exports (Revolut / Santander), categorizes transactions using Claude AI, and exports to Google Sheets using double-entry bookkeeping.

Built as a CLI first, now a full web app with a React frontend, FastAPI backend, and real-time WebSocket classification. Planned: live Revolut integration.

---

## What it does

- Reads any bank CSV (auto-detects delimiter, column names in Spanish/English)
- Classifies each transaction into a hierarchical chart of accounts using:
  1. Memory (`history.json`) — no API call
  2. Keyword rules — no API call
  3. Claude AI — when ambiguous
  4. User confirmation — when AI is uncertain (done in browser, not terminal)
- Exports results as double-entry bookkeeping rows to Google Sheets (`DIARIO AUTO`)
- Web UI: drag & drop CSV, live terminal log, searchable category picker, dashboard with charts

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11+, FastAPI, WebSockets, uvicorn |
| AI | Anthropic SDK — `claude-sonnet-4-20250514` |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, Recharts |
| Sheets | gspread + Google service account |
| Config | python-dotenv |

---

## Quick start

### 1. Python environment

```bash
cd pnl-ai
python3 -m venv .pnlai
source .pnlai/bin/activate
pip install -r requirements.txt
```

### 2. Environment variables

Create `.env` in the project root:

```env
ANTHROPIC_API_KEY=sk-ant-...

# Google Sheets (Phase 2)
GOOGLE_SHEETS_ID=1pdMN5xW7EIcz7Z7Rsu-By1kGelJhip4hJt83e8nBUyM
GOOGLE_CREDENTIALS_PATH=data/credentials.json

# Revolut (Phase 4 — not yet)
REVOLUT_WEBHOOK_SECRET=...
REVOLUT_API_KEY=...
```

For Google Sheets: create a service account in Google Cloud Console, enable the Sheets API, download the JSON key to `data/credentials.json`, and share your spreadsheet with the service account email.

### 3. Run the web app

```bash
# Terminal 1 — backend
source .pnlai/bin/activate
uvicorn backend.api:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

### 4. Or use the CLI

```bash
source .pnlai/bin/activate

# Classify and export to CSV
python main.py data/gastos-marzo.csv --account 211

# Classify + upload to Google Sheets
python main.py data/gastos-marzo.csv --account 211 --sheets

# Fully automatic (no prompts)
python main.py data/gastos-marzo.csv --account 211 --sheets --auto
```

---

## File structure

```
pnl-ai/
├── backend/
│   ├── api.py           # FastAPI: REST endpoints + WebSocket
│   └── ws_manager.py    # WebSocket session registry
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Upload.tsx     # CSV upload, live log, question cards
│       │   ├── Dashboard.tsx  # Charts, tables, Sheets upload, inline edits
│       │   └── History.tsx    # View/edit/delete history.json entries
│       ├── accounts.ts        # Account options + Sheets URL
│       ├── types.ts           # Shared TypeScript types
│       └── App.tsx            # Router
├── main.py              # CLI entry point (still fully functional)
├── classifier.py        # Core AI logic: history → keywords → Claude → ask
├── csv_reader.py        # Bank CSV parser (auto-detects delimiter + columns)
├── categories.py        # Chart of accounts + keyword hints — customize here
├── gsheets.py           # Google Sheets uploader (double-entry rows)
├── requirements.txt
├── .env                 # Never commit
└── data/
    ├── history.json     # Auto-created — learned classifications
    ├── credentials.json # Google service account key — never commit
    └── *.csv            # Your bank exports
```

---

## Web app pages

### Upload (`/`)
- Drag & drop a CSV file
- Select the asset account (e.g. `211 — Cuenta principal Jaime`)
- Click **Classify** → classification runs on the server
- Live terminal log at the bottom (same output as CLI)
- When AI is uncertain: an amber card appears with a searchable category picker — pick and classification continues
- On completion → automatically navigates to Dashboard

### Dashboard (`/dashboard`)
- Summary cards: total expenses / income / balance
- Bar chart by category group (Casa, Transporte, Salud & Ocio…)
- Category breakdown table
- Full transaction list — click ✏ on any row to correct the category inline
- **Open Sheets** button → direct link to your Google Sheets
- **Upload to Sheets** button → appends all rows (with your corrections)
- **History** button → navigate to History page

### History (`/history`)
- Full list of learned classifications from `history.json`
- Search by description or category
- Click ✏ to edit a category → searchable dropdown → saves immediately to `history.json`
- Delete any entry

---

## Customizing categories

Edit `categories.py` (never auto-modified by the app):

- `ACCOUNTS_PLAN` — your asset accounts (banks, investments, cash)
- `COSTS_PLAN` — expense and income categories
- `KEYWORD_HINTS` — map keywords → category code for instant classification without API

---

## Roadmap

| Phase | Status | Description |
|---|---|---|
| 1 — CLI | ✅ Done | CSV → classify → export CSV |
| 2 — Google Sheets | ✅ Done | Auto-upload double-entry rows |
| 3 — Web App | ✅ Done | React UI, WebSocket classification, dashboard, history editor |
| 4 — Live Revolut | ⬜ Next | Webhook receiver → real-time classify → push to dashboard |

---

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/api/classify` | Upload CSV + account, returns `session_id` |
| `WS` | `/ws/{session_id}` | Classification stream + interactive answers |
| `POST` | `/api/upload-sheets` | Append results to Google Sheets |
| `GET` | `/api/history` | List all history entries |
| `PATCH` | `/api/history/{key}` | Update a history entry's category |
| `DELETE` | `/api/history/{key}` | Delete a history entry |
| `GET` | `/api/categories` | List all leaf category codes + labels |
| `GET` | `/docs` | Auto-generated Swagger UI |
