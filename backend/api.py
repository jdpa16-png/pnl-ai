"""
FastAPI backend — Phase 3.
Endpoints:
  POST /api/classify          Upload CSV + account → returns session_id
  WS   /ws/{session_id}      Bidirectional: progress events out, answers in
  POST /api/upload-sheets     Upload results to Google Sheets
  GET  /api/history           Return full history.json
  PATCH /api/history/{key}    Update one entry's category
  DELETE /api/history/{key}   Delete one entry
  GET  /api/categories        Return all leaf category codes + labels
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote
from uuid import uuid4

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# Make root-level modules importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from categories import CATEGORIES, COSTS_PLAN
from classifier import ExpenseClassifier
from csv_reader import read_bank_csv
from gsheets import upload_to_sheets
from backend.ws_manager import manager
from backend.staging import append_results, clear as clear_staging, load_all as load_staging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pending jobs: session_id → (csv_path, account_code)
_pending: dict[str, tuple[Path, str]] = {}


# ─── REST ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def health() -> dict:
    return {"status": "ok", "service": "pnl-ai backend"}

@app.post("/api/classify")
async def start_classify(file: UploadFile, account: str = Form(...)) -> dict:
    """Saves the uploaded CSV and registers the classification job."""
    session_id = str(uuid4())

    suffix = Path(file.filename or "upload.csv").suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(await file.read())
    tmp.close()

    _pending[session_id] = (Path(tmp.name), account)
    return {"session_id": session_id}


HISTORY_PATH = Path(__file__).parent.parent / "data" / "history.json"


def _load_history() -> dict:
    if HISTORY_PATH.exists():
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    return {}


def _save_history(data: dict) -> None:
    HISTORY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


CATEGORIES_PY = Path(__file__).parent.parent / "categories.py"


@app.get("/api/categories")
async def get_categories() -> list[dict]:
    """Returns all leaf category codes and labels."""
    return [{"code": c, "label": COSTS_PLAN.get(c, c)} for c in CATEGORIES]


@app.get("/api/categories/plan")
async def get_categories_plan() -> dict:
    """Returns the full COSTS_PLAN dict (all codes including group headers)."""
    return COSTS_PLAN


@app.patch("/api/categories/{code:path}")
async def update_category_label(code: str, payload: dict) -> dict:
    """Updates a category label directly in categories.py."""
    import re
    new_label = payload.get("label", "").strip()
    if not new_label:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="label is required")

    source = CATEGORIES_PY.read_text(encoding="utf-8")
    # Replace the exact line: "CODE": "old label",
    pattern = rf'("{re.escape(code)}":\s*)"[^"]*"'
    replacement = rf'\g<1>"{new_label}"'
    updated, count = re.subn(pattern, replacement, source)
    if count == 0:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Code '{code}' not found in categories.py")

    CATEGORIES_PY.write_text(updated, encoding="utf-8")
    # Reload the in-memory plan so subsequent API calls reflect the change
    import importlib, categories as cats_module
    importlib.reload(cats_module)
    return {"ok": True, "code": code, "label": new_label}


@app.get("/api/history")
async def get_history() -> list[dict]:
    """Returns all history entries as a list."""
    history = _load_history()
    return [{"key": k, **v} for k, v in history.items()]


@app.patch("/api/history/{key:path}")
async def update_history_entry(key: str, payload: dict) -> dict:
    """Updates the category of a history entry."""
    key = unquote(key)
    history = _load_history()
    if key not in history:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Entry not found")
    history[key]["category"] = payload["category"]
    _save_history(history)
    return {"ok": True}


@app.delete("/api/history/{key:path}")
async def delete_history_entry(key: str) -> dict:
    """Removes a history entry."""
    key = unquote(key)
    history = _load_history()
    history.pop(key, None)
    _save_history(history)
    return {"ok": True}


@app.get("/api/staging")
async def get_staging() -> list[dict]:
    """Returns all transactions currently in the staging file."""
    return await asyncio.to_thread(load_staging)


@app.post("/api/upload-sheets")
async def upload_sheets(payload: dict) -> dict:
    """Appends classified results to Google Sheets, then clears the staging file."""
    results = payload.get("results", [])
    account = payload.get("account")
    rows = upload_to_sheets(results, account_code=account)
    await asyncio.to_thread(clear_staging)
    return {"rows_added": rows, "staging_cleared": True}


# ─── WEBSOCKET ─────────────────────────────────────────────────────────────────

@app.websocket("/ws/{session_id}")
async def ws_endpoint(ws: WebSocket, session_id: str) -> None:
    await manager.connect(session_id, ws)
    try:
        job = _pending.pop(session_id, None)
        if not job:
            await ws.send_json({"type": "error", "message": "Session not found"})
            return

        csv_path, account = job
        loop = asyncio.get_event_loop()

        # ── Async/sync bridge ─────────────────────────────────────────────────

        def sync_ask(tx: dict, ai_result: dict) -> str:
            """Called from the classifier thread; bridges to the async WS layer."""
            options = [{"code": c, "label": COSTS_PLAN.get(c, c)} for c in CATEGORIES]
            question = {
                "type": "question",
                "transaction": {
                    "date": tx.get("date", ""),
                    "description": tx.get("description", ""),
                    "amount": tx.get("amount", 0),
                },
                "suggestion": ai_result.get("category", ""),
                "reason": ai_result.get("reason", ""),
                "options": options,
            }
            asyncio.run_coroutine_threadsafe(
                manager.send(session_id, question), loop
            ).result(timeout=10)

            future = asyncio.run_coroutine_threadsafe(
                manager.wait_for_answer(session_id), loop
            )
            return future.result(timeout=300)

        def sync_progress(index: int, total: int, tx: dict, result: dict) -> None:
            """Called from the classifier thread after each transaction."""
            cat_code = result.get("category", "")
            asyncio.run_coroutine_threadsafe(
                manager.send(session_id, {
                    "type": "progress",
                    "index": index,
                    "total": total,
                    "transaction": {
                        "date": tx.get("date", ""),
                        "description": tx.get("description", ""),
                        "amount": tx.get("amount", 0),
                        "category": cat_code,
                        "category_label": COSTS_PLAN.get(cat_code, ""),
                        "confidence": result.get("confidence", ""),
                        "method": result.get("source", "ai"),
                    },
                }),
                loop,
            )

        # ── Run classification in thread so we don't block the event loop ─────

        async def run_classification() -> None:
            transactions = read_bank_csv(csv_path)
            classifier = ExpenseClassifier(
                history_path=str(Path(__file__).parent.parent / "data" / "history.json"),
                interactive=True,
                ask_fn=sync_ask,
            )
            results = await asyncio.to_thread(
                classifier.classify_batch, transactions, sync_progress
            )
            # Stamp the asset account onto every result before staging
            for r in results:
                r.setdefault("account_code", account)
            duplicates = await asyncio.to_thread(append_results, results)
            await manager.send(session_id, {
                "type": "done",
                "results": results,
                "duplicates": duplicates,
            })

        classify_task = asyncio.create_task(run_classification())

        # ── Receive answers from browser ──────────────────────────────────────
        while True:
            try:
                data = await ws.receive_json()
                if data.get("type") == "answer":
                    await manager.put_answer(session_id, data["category"])
            except WebSocketDisconnect:
                classify_task.cancel()
                break

    finally:
        manager.disconnect(session_id)
