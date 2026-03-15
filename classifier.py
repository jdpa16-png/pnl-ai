"""
Expense classifier using Claude API.
- Uses previous history to learn from your categorizations
- Applies keywords for obvious cases (no API cost)
- Asks interactively when confidence is low
"""
from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path

import anthropic

from categories import ACCOUNTS_PLAN, ASSET_ACCOUNTS, CATEGORIES, COSTS_PLAN, KEYWORD_HINTS


# Confidence threshold for asking the user (0-1)
CONFIDENCE_THRESHOLD = 0.75


class ExpenseClassifier:
    def __init__(
        self,
        history_path: str = "data/history.json",
        interactive: bool = True,
        ask_fn: "Callable[[dict, dict], str] | None" = None,
    ):
        """
        Args:
            ask_fn: Optional callback for web mode. Signature: (tx, ai_result) -> category_code.
                    When set, replaces the CLI input() prompt. Must be a blocking (sync) callable
                    that internally bridges to the async WebSocket layer.
        """
        self.interactive = interactive
        self.ask_fn = ask_fn
        self.history_path = Path(history_path)
        self.history = self._load_history()
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # ──────────────────────────────────────────────────────────────────────────
    # MAIN CLASSIFICATION
    # ──────────────────────────────────────────────────────────────────────────

    def classify_batch(
        self,
        transactions: list[dict],
        on_progress: "Callable[[int, int, dict, dict], None] | None" = None,
    ) -> list[dict]:
        """
        Classifies a list of transactions.

        Args:
            on_progress: Optional callback called after each transaction.
                         Signature: (index, total, tx, result) -> None.
                         Used by web mode to push progress via WebSocket.
        """
        results = []
        total = len(transactions)

        for i, tx in enumerate(transactions):
            print(f"[{i+1}/{total}] {tx['date']} | {tx['description'][:45]:<45} | {tx['amount']:>9.2f} €", end="  ")

            result = self.classify_one(tx)
            merged = {**tx, **result}
            results.append(merged)

            confidence_emoji = "✅" if result["confidence"] == "high" else "🟡" if result["confidence"] == "medium" else "❓"
            source_label = {"history": "hist", "keyword": "kw", "ai": "ai", "user": "user", "error": "err"}.get(result.get("source", ""), "?")
            print(f"{confidence_emoji} [{source_label}|{result['confidence']}] {result['category']}")

            if on_progress:
                on_progress(i + 1, total, tx, result)

        # Save updated history
        self._save_history()
        return results

    def classify_one(self, tx: dict) -> dict:
        """
        Classifies a single transaction.
        Strategy:
        1. Exact history lookup
        2. Keyword match
        3. Claude API
        4. If low confidence and interactive mode → ask user
        """
        description = tx["description"]
        amount = tx["amount"]

        # 1. Exact history match
        hist_result = self._lookup_history(description)
        if hist_result:
            return {
                "category": hist_result["category"],
                "source_account": hist_result.get("source_account", "Actual"),
                "confidence": "high",
                "source": "history",
            }

        # 2. Quick keyword match
        keyword_cat = self._keyword_match(description)
        if keyword_cat:
            result = {
                "category": keyword_cat,
                "source_account": "Actual",
                "confidence": "high",
                "source": "keyword",
            }
            self._add_to_history(description, result)
            return result

        # 3. Claude API
        ai_result = self._classify_with_ai(tx)

        # 4. If low confidence and interactive → ask user
        if self.interactive and ai_result["confidence"] in ("low", "medium"):
            ai_result = self._ask_user(tx, ai_result)

        self._add_to_history(description, ai_result)
        return ai_result

    # ──────────────────────────────────────────────────────────────────────────
    # CLAUDE API
    # ──────────────────────────────────────────────────────────────────────────

    def _classify_with_ai(self, tx: dict) -> dict:
        """Calls Claude to categorize the transaction."""

        categories_str = "\n".join(
            f"  {code}: {COSTS_PLAN[code]}" for code in CATEGORIES
        )
        accounts_str = "\n".join(
            f"  [{k}] {v}" for k, v in ACCOUNTS_PLAN.items() if len(k) == 3
        )

        # Recent history context so Claude learns your patterns
        history_examples = self._get_history_examples(10)
        history_str = ""
        if history_examples:
            history_str = "\nExamples of previous categorizations:\n"
            for h in history_examples:
                history_str += f"  '{h['description']}' → {h['category']}\n"

        prompt = f"""You are an assistant that categorizes personal bank transactions.

TRANSACTION TO CATEGORIZE:
- Description: {tx['description']}
- Amount: {tx['amount']} {tx.get('currency', 'EUR')}
- Operation type: {tx.get('type', 'unknown')}
- Date: {tx.get('date', '')}

AVAILABLE CATEGORIES (reply with the code only, e.g. "441"):
{categories_str}

AVAILABLE ASSET ACCOUNTS (code + name):
{accounts_str}
{history_str}

Reply ONLY with valid JSON (no markdown) in this exact format:
{{
  "category": "exact category name",
  "source_account": "account name",
  "confidence": "high|medium|low",
  "reason": "brief one-sentence explanation"
}}

Rules:
- "confidence" is "high" if very certain, "medium" if unsure, "low" if very ambiguous
- A positive amount is likely income
- A negative amount is likely an expense
- "source_account" is the account the money comes from (usually "Actual")
"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()
            # Strip possible backticks
            response_text = response_text.replace("```json", "").replace("```", "").strip()

            data = json.loads(response_text)

            # Validate category code exists
            if data.get("category") not in COSTS_PLAN:
                data["category"] = "OTR"
                data["confidence"] = "low"

            return {
                "category": data.get("category", "Uncategorized"),
                "source_account": data.get("source_account", "Actual"),
                "confidence": data.get("confidence", "medium"),
                "reason": data.get("reason", ""),
                "source": "ai",
            }

        except Exception as e:
            print(f"\n⚠️  API error: {e}")
            return {
                "category": "Uncategorized",
                "source_account": "Actual",
                "confidence": "low",
                "source": "error",
            }

    # ──────────────────────────────────────────────────────────────────────────
    # USER INTERACTION
    # ──────────────────────────────────────────────────────────────────────────

    def _ask_user(self, tx: dict, ai_result: dict) -> dict:
        """
        Asks the user when the AI is uncertain.
        In web mode (ask_fn set): calls ask_fn which blocks until frontend responds.
        In CLI mode: uses input() as before.
        """
        if self.ask_fn:
            # Web mode: delegate to the async bridge (blocking from this thread's perspective)
            chosen = self.ask_fn(tx, ai_result)
            ai_result["category"] = chosen
            ai_result["confidence"] = "high"
            ai_result["source"] = "user"
            return ai_result

        # CLI mode (original behaviour)
        print(f"\n  ┌─ 🤔 Unsure about: '{tx['description']}' ({tx['amount']} €)")
        print(f"  │  AI suggests: '{ai_result['category']}' (confidence: {ai_result['confidence']})")
        if ai_result.get("reason"):
            print(f"  │  Reason: {ai_result['reason']}")
        print(f"  └─ Options:")

        for i, code in enumerate(CATEGORIES, 1):
            desc = COSTS_PLAN.get(code, code)
            marker = "👉" if code == ai_result["category"] else "  "
            print(f"     {marker} {i:2}. {code}: {desc}")

        print(f"\n  Press ENTER to accept '{ai_result['category']}'")
        print(f"  Or type the category number: ", end="")

        try:
            user_input = input().strip()

            if not user_input:
                ai_result["confidence"] = "high"
                return ai_result

            idx = int(user_input) - 1
            if 0 <= idx < len(CATEGORIES):
                ai_result["category"] = CATEGORIES[idx]
                ai_result["confidence"] = "high"
                ai_result["source"] = "user"
            else:
                print("  ⚠️  Invalid number, using AI suggestion")

        except (ValueError, EOFError):
            pass

        return ai_result

    # ──────────────────────────────────────────────────────────────────────────
    # HISTORY / MEMORY
    # ──────────────────────────────────────────────────────────────────────────

    def _load_history(self) -> dict:
        """Loads the previous categorizations history."""
        if self.history_path.exists():
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_history(self):
        """Saves the updated history."""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def _lookup_history(self, description: str) -> dict | None:
        """Looks up an exact description in the history."""
        key = description.lower().strip()
        return self.history.get(key)

    def _add_to_history(self, description: str, result: dict):
        """Adds a categorization to the history."""
        # Only save if high confidence (don't learn from mistakes)
        if result.get("confidence") == "high":
            key = description.lower().strip()
            self.history[key] = {
                "description": description,
                "category": result["category"],
                "source_account": result.get("source_account", "Actual"),
            }

    def _get_history_examples(self, n: int = 10) -> list[dict]:
        """Returns N examples from the history for the prompt."""
        items = list(self.history.values())
        return items[-n:] if len(items) > n else items

    # ──────────────────────────────────────────────────────────────────────────
    # KEYWORDS
    # ──────────────────────────────────────────────────────────────────────────

    def _keyword_match(self, description: str) -> str | None:
        """Looks for keywords in the description for fast categorization."""
        desc_lower = description.lower()
        for keyword, category in KEYWORD_HINTS.items():
            if keyword in desc_lower:
                return category
        return None
