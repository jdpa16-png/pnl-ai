"""
Clasificador de gastos usando Claude API.
- Usa historial previo para aprender de tus categorizaciones
- Aplica keywords para casos obvios (sin gastar API)
- Pregunta interactivamente cuando la confianza es baja
"""

import json
import os
from pathlib import Path

import anthropic

from categories import CATEGORIES, EXPENSE_CATEGORIES, INCOME_CATEGORIES, KEYWORD_HINTS


# Umbral de confianza para preguntar al usuario (0-1)
CONFIDENCE_THRESHOLD = 0.75


class ExpenseClassifier:
    def __init__(self, historial_path: str = "data/historial.json", interactive: bool = True):
        self.interactive = interactive
        self.historial_path = Path(historial_path)
        self.historial = self._load_historial()
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # ──────────────────────────────────────────────────────────────────────────
    # CLASIFICACIÓN PRINCIPAL
    # ──────────────────────────────────────────────────────────────────────────

    def classify_batch(self, movimientos: list[dict]) -> list[dict]:
        """Clasifica una lista de movimientos."""
        resultados = []
        total = len(movimientos)

        for i, mov in enumerate(movimientos):
            print(f"[{i+1}/{total}] {mov['fecha']} | {mov['descripcion'][:45]:<45} | {mov['importe']:>9.2f} €", end="  ")

            resultado = self.classify_one(mov)
            resultados.append({**mov, **resultado})

            confianza_emoji = "✅" if resultado["confianza"] == "alta" else "🟡" if resultado["confianza"] == "media" else "❓"
            print(f"{confianza_emoji} {resultado['categoria']}")

        # Guardar historial actualizado
        self._save_historial()
        return resultados

    def classify_one(self, mov: dict) -> dict:
        """
        Clasifica un movimiento individual.
        Estrategia:
        1. Buscar en historial exacto
        2. Buscar por keyword
        3. Preguntar a Claude API
        4. Si confianza baja y modo interactivo → preguntar al usuario
        """
        descripcion = mov["descripcion"]
        importe = mov["importe"]

        # 1. Historial exacto
        hist_result = self._lookup_historial(descripcion)
        if hist_result:
            return {
                "categoria": hist_result["categoria"],
                "cuenta_origen": hist_result.get("cuenta_origen", "Actual"),
                "confianza": "alta",
                "fuente": "historial",
            }

        # 2. Keywords rápidas
        keyword_cat = self._keyword_match(descripcion)
        if keyword_cat:
            result = {
                "categoria": keyword_cat,
                "cuenta_origen": "Actual",
                "confianza": "alta",
                "fuente": "keyword",
            }
            self._add_to_historial(descripcion, result)
            return result

        # 3. Claude API
        ai_result = self._classify_with_ai(mov)

        # 4. Si confianza baja y modo interactivo → preguntar
        if self.interactive and ai_result["confianza"] in ("baja", "media"):
            ai_result = self._ask_user(mov, ai_result)

        self._add_to_historial(descripcion, ai_result)
        return ai_result

    # ──────────────────────────────────────────────────────────────────────────
    # CLAUDE API
    # ──────────────────────────────────────────────────────────────────────────

    def _classify_with_ai(self, mov: dict) -> dict:
        """Llama a Claude para categorizar el movimiento."""
        
        categorias_str = "\n".join(f"- {c}" for c in CATEGORIES)
        cuentas_str = "Actual, Revolut, Efectivo, Ahorro"
        
        # Contexto del historial reciente para que aprenda tu patrón
        historial_ejemplos = self._get_historial_examples(10)
        historial_str = ""
        if historial_ejemplos:
            historial_str = "\nEjemplos de categorizaciones previas del usuario:\n"
            for h in historial_ejemplos:
                historial_str += f"  '{h['descripcion']}' → {h['categoria']}\n"

        prompt = f"""Eres un asistente que categoriza movimientos bancarios personales en español.

MOVIMIENTO A CATEGORIZAR:
- Descripción: {mov['descripcion']}
- Importe: {mov['importe']} {mov.get('divisa', 'EUR')}
- Tipo operación: {mov.get('tipo', 'desconocido')}
- Fecha: {mov.get('fecha', '')}

CATEGORÍAS DISPONIBLES:
{categorias_str}

CUENTAS DE ACTIVO DISPONIBLES:
{cuentas_str}
{historial_str}

Responde ÚNICAMENTE con un JSON válido (sin markdown) con este formato exacto:
{{
  "categoria": "nombre exacto de la categoría",
  "cuenta_origen": "nombre de la cuenta",
  "confianza": "alta|media|baja",
  "razon": "explicación breve en una frase"
}}

Reglas:
- "confianza" es "alta" si estás muy seguro, "media" si hay dudas, "baja" si es muy ambiguo
- Si el importe es positivo probablemente es un ingreso
- Si el importe es negativo probablemente es un gasto
- "cuenta_origen" es la cuenta de donde sale el dinero (normalmente "Actual")
"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            # Limpiar posibles backticks
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(response_text)
            
            # Validar que la categoría existe
            if data.get("categoria") not in CATEGORIES:
                data["categoria"] = "Sin categorizar"
                data["confianza"] = "baja"
            
            return {
                "categoria": data.get("categoria", "Sin categorizar"),
                "cuenta_origen": data.get("cuenta_origen", "Actual"),
                "confianza": data.get("confianza", "media"),
                "razon": data.get("razon", ""),
                "fuente": "ai",
            }

        except Exception as e:
            print(f"\n⚠️  Error en API: {e}")
            return {
                "categoria": "Sin categorizar",
                "cuenta_origen": "Actual",
                "confianza": "baja",
                "fuente": "error",
            }

    # ──────────────────────────────────────────────────────────────────────────
    # INTERACCIÓN CON USUARIO
    # ──────────────────────────────────────────────────────────────────────────

    def _ask_user(self, mov: dict, ai_result: dict) -> dict:
        """Pregunta al usuario cuando la IA no está segura."""
        print(f"\n  ┌─ 🤔 Duda en: '{mov['descripcion']}' ({mov['importe']} €)")
        print(f"  │  IA sugiere: '{ai_result['categoria']}' (confianza: {ai_result['confianza']})")
        if ai_result.get("razon"):
            print(f"  │  Razón: {ai_result['razon']}")
        print(f"  └─ Opciones:")
        
        # Mostrar categorías numeradas
        for i, cat in enumerate(CATEGORIES, 1):
            marker = "👉" if cat == ai_result["categoria"] else "  "
            print(f"     {marker} {i:2}. {cat}")
        
        print(f"\n  Pulsa ENTER para aceptar '{ai_result['categoria']}'")
        print(f"  O escribe el número de categoría: ", end="")
        
        try:
            user_input = input().strip()
            
            if not user_input:
                # Aceptar sugerencia de IA
                ai_result["confianza"] = "alta"  # El usuario validó
                return ai_result
            
            idx = int(user_input) - 1
            if 0 <= idx < len(CATEGORIES):
                ai_result["categoria"] = CATEGORIES[idx]
                ai_result["confianza"] = "alta"
                ai_result["fuente"] = "usuario"
            else:
                print("  ⚠️  Número inválido, usando sugerencia de IA")
                
        except (ValueError, EOFError):
            pass  # Mantener resultado de IA
        
        return ai_result

    # ──────────────────────────────────────────────────────────────────────────
    # HISTORIAL / MEMORIA
    # ──────────────────────────────────────────────────────────────────────────

    def _load_historial(self) -> dict:
        """Carga el historial de categorizaciones previas."""
        if self.historial_path.exists():
            with open(self.historial_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_historial(self):
        """Guarda el historial actualizado."""
        self.historial_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.historial_path, "w", encoding="utf-8") as f:
            json.dump(self.historial, f, ensure_ascii=False, indent=2)

    def _lookup_historial(self, descripcion: str) -> dict | None:
        """Busca una descripción exacta en el historial."""
        key = descripcion.lower().strip()
        return self.historial.get(key)

    def _add_to_historial(self, descripcion: str, result: dict):
        """Añade una categorización al historial."""
        # Solo guardar si confianza alta (no queremos aprender errores)
        if result.get("confianza") == "alta":
            key = descripcion.lower().strip()
            self.historial[key] = {
                "descripcion": descripcion,
                "categoria": result["categoria"],
                "cuenta_origen": result.get("cuenta_origen", "Actual"),
            }

    def _get_historial_examples(self, n: int = 10) -> list[dict]:
        """Devuelve N ejemplos del historial para el prompt."""
        items = list(self.historial.values())
        return items[-n:] if len(items) > n else items

    # ──────────────────────────────────────────────────────────────────────────
    # KEYWORDS
    # ──────────────────────────────────────────────────────────────────────────

    def _keyword_match(self, descripcion: str) -> str | None:
        """Busca keywords en la descripción para categorización rápida."""
        desc_lower = descripcion.lower()
        for keyword, categoria in KEYWORD_HINTS.items():
            if keyword in desc_lower:
                return categoria
        return None
