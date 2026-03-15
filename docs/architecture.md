# Architecture

## System overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  INPUT                                                               │
│  Bank CSV (Revolut / Santander)        Revolut webhook (Phase 4)    │
└──────────────────────┬──────────────────────────┬───────────────────┘
                       │                          │
              csv_reader.py                  revolut.py (Phase 4)
                       │                          │
                       └──────────┬───────────────┘
                                  ▼
                           classifier.py
                      ┌────────────────────┐
                      │ 1. history.json     │ → high confidence, no API
                      │ 2. keyword hints    │ → high confidence, no API
                      │ 3. Claude API       │ → returns category + confidence
                      │ 4. uncertain?       │
                      │    CLI  → input()   │
                      │    Web  → WebSocket │ → browser question card
                      └────────────────────┘
                                  │
                    ┌─────────────┼──────────────┐
                    ▼             ▼              ▼
               CSV export    gsheets.py     WS → Dashboard
               (main.py)    (DIARIO AUTO)   (React frontend)
```

The same `classifier.py` core serves both CLI and Web modes.
The only difference is the `ask_fn` callback: `None` = CLI `input()`, provided = WebSocket bridge.

---

## Classification pipeline

| Step                             | Source    | API call?           | Saved to history?       |
|----------------------------------|-----------|---------------------|-------------------------|
| Exact match in `history.json`    | `history` | No                  | Already there           |
| Keyword match in `KEYWORD_HINTS` | `keyword` | No                  | Yes (high)              |
| Claude API                       | `ai`      | Yes                 | Only if high confidence |
| User corrects AI                 | `user`    | No (already called) | Yes (high)    |

History key = `description.lower().strip()`. Only `confidence == "high"` entries are saved.

---

## Web app — request/event flow

```
Browser                          FastAPI (port 8000)              Thread pool
   │                                    │                              │
   │── POST /api/classify ─────────────►│                              │
   │◄─ { session_id } ───────────────── │                              │
   │                                    │                              │
   │── WS /ws/{session_id} ────────────►│                              │
   │                                    │── asyncio.to_thread ────────►│
   │                                    │   classify_batch()           │
   │◄── { type: progress, ... } ────────│◄─ sync_progress callback ───│
   │◄── { type: progress, ... } ────────│◄─ ...                       │
   │                                    │                              │
   │◄── { type: question, ... } ────────│◄─ sync_ask: blocks thread ──│
   │── { type: answer, category } ─────►│                              │
   │                                    │── put_answer ───────────────►│ (unblocks)
   │                                    │                              │
   │◄── { type: done, results } ────────│◄─ returns all results ──────│
   │                                    │
   │── POST /api/upload-sheets ────────►│── gsheets.py
   │◄─ { rows_added } ─────────────────│
```

---

## Async/sync bridge (key design detail)

`classify_batch` runs in a worker thread via `asyncio.to_thread`.
When the classifier needs a user answer, it calls `sync_ask(tx, ai_result)` which:

1. Calls `run_coroutine_threadsafe(manager.send(session_id, question), loop).result()` — sends question to browser from the thread
2. Calls `run_coroutine_threadsafe(manager.wait_for_answer(session_id), loop).result(timeout=300)` — blocks the thread (not the event loop) waiting for the browser's answer
3. The WS handler receives `{"type": "answer", "category": "512"}` and calls `await manager.put_answer(session_id, "512")`
4. Step 2 unblocks, returns `"512"`, classification continues

This keeps `classifier.py` fully synchronous while enabling real async WebSocket interaction.

---

## Frontend pages

### `/` — Upload & Classify
```
┌──────────────────────────────────────────────┐
│  CSV drag & drop zone                        │
│  Account selector (3-digit leaf accounts)    │
│  [Classify] button                           │
├──────────────────────────────────────────────┤
│  Progress bar                [n / total]     │
│                                              │
│  ┌─ Amber question card (when AI unsure) ─┐  │
│  │  Transaction + AI reason               │  │
│  │  Search input                          │  │
│  │  2-col grid of category buttons        │  │
│  └────────────────────────────────────────┘  │
├──────────────────────────────────────────────┤
│  Terminal log panel (macOS style chrome)     │
│  [1/25] 2026-03-09 | VIVETIX  | -62.67 €  ✅│
│  [2/25] 2026-03-09 | DIA      |  -6.58 €  ✅│
│    🤔 Unsure: "Gato Tuerto" (-10.00 €)       │
│    → You chose: 512                          │
└──────────────────────────────────────────────┘
```

### `/dashboard` — Results
```
┌────────────────┬─────────────────┬──────────────┐
│ Total expenses │  Total income   │   Balance    │
└────────────────┴─────────────────┴──────────────┘
┌──────────────────────────────────────────────────┐
│  Bar chart — expenses grouped by category group  │
└──────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────┐
│  Category breakdown table                        │
└──────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────┐
│  All transactions — category column is editable  │
│  Click ✏ → searchable dropdown → updates result  │
│  "Upload to Sheets" uses corrected categories    │
└──────────────────────────────────────────────────┘
  Buttons: [Open Sheets] [⬆ Upload to Sheets] [📚 History] [← New file]
```

### `/history` — History editor
```
Search: [________________]
┌───────────────────────────────────┬─────────────────┬─────────┐
│ Description                       │ Category        │ Actions │
├───────────────────────────────────┼─────────────────┼─────────┤
│ DIA                               │ 441 Supermercado│ Delete  │
│ Repsol                            │ 731 Gasolina ✏  │ Delete  │
│   → click ✏: search + dropdown    │                 │         │
└───────────────────────────────────┴─────────────────┴─────────┘
```
Edits write immediately to `data/history.json` via `PATCH /api/history/{key}`.

---

## REST API

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check `{"status":"ok"}` |
| `POST` | `/api/classify` | Upload CSV + account → `{session_id}` |
| `WS` | `/ws/{session_id}` | Classification stream + answer channel |
| `POST` | `/api/upload-sheets` | Append results to Google Sheets |
| `GET` | `/api/history` | List all history entries |
| `PATCH` | `/api/history/{key}` | Update one entry's category |
| `DELETE` | `/api/history/{key}` | Delete one entry |
| `GET` | `/api/categories` | All leaf category codes + labels |
| `GET` | `/docs` | Swagger UI (FastAPI auto-generated) |

---

## Export format — double-entry bookkeeping

Output columns: `code`, `description`, `date`, `movement_description`, `amount`

**Expense** (amount < 0):
- Row 1 — FROM asset: `asset_code`, asset name, date, desc, `-abs(amount)`
- Row 2 — TO cost:   category code, category name, date, desc, `+abs(amount)`

**Income** (amount > 0):
- Row 1 — FROM income: category code, category name, date, desc, `-amount`
- Row 2 — TO asset:    `asset_code`, asset name, date, desc, `+amount`

Target sheet: `DIARIO AUTO` in the configured Google Spreadsheet.

---

## Module responsibilities

| File | Role |
|---|---|
| `main.py` | CLI entry point, CSV export, summary, `--sheets` flag |
| `backend/api.py` | FastAPI app — all REST routes + WebSocket endpoint |
| `backend/ws_manager.py` | Session WebSocket registry; `send`, `wait_for_answer`, `put_answer` |
| `classifier.py` | Full classification logic with pluggable `ask_fn` + `on_progress` callbacks |
| `csv_reader.py` | Bank CSV parser — auto-detects `,`/`;` delimiter + ES/EN column names |
| `categories.py` | `COSTS_PLAN`, `ACCOUNTS_PLAN`, `KEYWORD_HINTS` — user-owned, never auto-modified |
| `gsheets.py` | Authenticates with service account, appends double-entry rows |
| `frontend/src/pages/Upload.tsx` | CSV upload, progress bar, question cards, terminal log |
| `frontend/src/pages/Dashboard.tsx` | Charts, summary, inline editing, Sheets upload |
| `frontend/src/pages/History.tsx` | View/edit/delete history.json via REST |
| `frontend/src/accounts.ts` | Hard-coded account options + Sheets URL constant |

---

## Phase 4 — Live Revolut (next)

```
Revolut servers
      │
      │  POST /webhook/revolut
      │  X-Revolut-Signature: HMAC-SHA256
      ▼
backend/revolut.py
  1. Verify HMAC signature (REVOLUT_WEBHOOK_SECRET)
  2. Parse transaction event → normalized dict (same shape as csv_reader output)
  3. Call classifier.classify_one(tx)  [already async-bridge-compatible]
  4. Push to all connected WS clients: {"type": "live_tx", "transaction": ...}
  5. Append to Google Sheets via gsheets.py

Dashboard.tsx (new section)
  - Live feed: receives "live_tx" events and prepends to a recent transactions list
  - If uncertain: same question card flow as CSV mode
```

New env vars needed:
```
REVOLUT_WEBHOOK_SECRET=...   # For HMAC verification
REVOLUT_API_KEY=...          # If polling is also needed
```

---

## CLI flags (main.py)

| Flag | Short | Default | Description |
|---|---|---|---|
| `--output` | `-o` | `categorized_transactions.csv` | Output CSV path |
| `--history` | | `data/history.json` | History file path |
| `--auto` | | `false` | Never prompt, always use best AI estimate |
| `--account` | `-a` | `???` | 3-digit asset account code from `ACCOUNTS_PLAN` |
| `--sheets` | | `false` | Upload results to Google Sheets after classifying |
