"""
Define your expense/income categories and asset accounts here.
Customize COSTS_PLAN and KEYWORD_HINTS to match your setup.
"""
from __future__ import annotations


# ─── ACCOUNTS PLAN (Grupo 2 — ACTIVO) ────────────────────────────────────────
# Hierarchical chart of asset accounts. Keys are string codes, values are descriptions.
# Groups (1 digit): headers. Sections (2 digits): sub-groups. Accounts (3+ digits): leaf nodes.
ACCOUNTS_PLAN: dict[str, str] = {
    # ── Grupo 2: ACTIVO ──────────────────────────────────────────────────────
    "2":   "ACTIVO",

    "20":  "EFECTIVO",
    "201": "Efectivo Euros",
    "202": "Efectivo Dólares",

    "21":  "CUENTAS SANTANDER",
    "211": "Cuenta principal Jaime",
    "212": "Cuenta principal Palo",

    "22":  "CUENTAS REVOLUT",
    "221": "Cuenta Revolut Jaime",
    "222": "Tarjeta Crédito Jaime Revolut",
    "223": "Cuenta Revolut Palo",
    "224": "Cuenta Compartida",

    "23":  "INVERSIONES",
    "231": "Abante",
    "232": "MyInvestor (Para Invertir)",
    "233": "MyInvestor (Invertido)",
    "234": "Axa - Plan Jaime",
    "235": "Santander - Depósito de custodia",

    "24":  "TARJETAS TRABAJO",
    "241": "Tarjeta Ticket Restaurante",
    "242": "Tarjeta Ticket Transporte",

    "25":  "ACTIVOS A CORTO/LARGO PLAZO",
    "250": "Bizums Pendientes",
    "251": "Adelantos Familia",

    "26":  "ACTIVOS INTANGIBLES",
    "261": "Caza",
    "262": "Licencia Caza",
    "263": "Seguro Caza",
    "264": "Licencia Coto",
    "265": "Permiso de Daños",
    "266": "Deporte",
    "267": "Federación Golf",
    "268": "Puerta de Hierro",
    "269": "Pachampions",
    "270": "Tarjetas Amazon",
}

# Leaf asset accounts (3-digit codes) — used by AI to assign source_account
ASSET_ACCOUNTS: list[str] = [v for k, v in ACCOUNTS_PLAN.items() if len(k) == 3]


# ─── COSTS PLAN (Grupos 4–9 — GASTOS E INGRESOS) ─────────────────────────────
# Same structure: 1-digit = group header, 2-digit = sub-group, 3+ digit = leaf.
# Alphanumeric codes (SU-J, ABN…) are income leaf nodes.
#
# Notes on simplifications vs. original proposal:
#   - Duplicate code 432 fixed: Netflix=432, Claude=433, Spotify=434, Other=435
#   - Two "Grupo 8" merged: SALUD/OCIO keeps 80-82; GASTOS FINANCIEROS becomes Grupo 9
#   - Code 72 (DEPORTE) moved to 82 to fit numerically under Grupo 8
#   - Grupo 9 income codes replaced with alphanumeric (OTR, SU-J…) to avoid conflict
COSTS_PLAN: dict[str, str] = {

    # ── Grupo 4: GASTOS DE CASA ───────────────────────────────────────────────
    "4":   "GASTOS DE CASA",

    "40":  "GASTOS VIVIENDA",
    "401": "Alquiler casa",

    "41":  "SUMINISTROS",
    "411": "Agua",
    "412": "Luz",
    "413": "Gas",
    "414": "Internet",

    "42":  "SEGUROS",
    "421": "Seguro Coche",
    "422": "Seguro Casa",
    "423": "Seguro Vida",

    "43":  "SUSCRIPCIONES",
    "431": "Suscripción Apple",
    "432": "Suscripción Netflix",
    "433": "Suscripción Claude",
    "434": "Suscripción Spotify",
    "435": "Otras suscripciones",

    "44":  "COMPRAS CASA",
    "441": "Compra general Supermercado",
    "442": "Compra Carrefour Express",
    "443": "Compra necesaria para casa",

    "45":  "PUCHO",
    "451": "Veterinario",

    # ── Grupo 5: COMER Y BEBER FUERA ─────────────────────────────────────────
    "5":   "COMER Y BEBER FUERA DE CASA",

    "50":  "COMIDA OFICINA",
    "501": "Comida regular Oficina",

    "51":  "COMIDA SOCIAL",
    "511": "Comida / Cena Juntos",
    "512": "Comida / Cena con amigos",

    # ── Grupo 6: COMPRAS Y TRANSFERENCIAS ────────────────────────────────────
    "6":   "COMPRAS Y TRANSFERENCIAS",

    "62":  "REGALOS",
    "621": "Regalos amigos",
    "622": "Regalos familia",

    "63":  "TRANSFERENCIAS",
    "631": "Bizum y transferencias a personas",

    # ── Grupo 7: TRANSPORTE ───────────────────────────────────────────────────
    "7":   "TRANSPORTE",

    "71":  "TRANSPORTE RENTING",
    "711": "Motos",
    "712": "Coches",
    "713": "Taxis",
    "714": "Transporte público",

    "73":  "TRANSPORTE PRIVADO",
    "731": "Gasolina",
    "732": "Gastos coche",
    "735": "ITV",

    # ── Grupo 8: SALUD Y OCIO ─────────────────────────────────────────────────
    "8":   "SALUD Y OCIO",

    "80":  "GASTOS SANIDAD",
    "801": "Salud",

    "81":  "GASTOS VIAJES",
    "811": "Viajes",

    "82":  "GASTOS DEPORTE",
    "821": "Deporte",
    "822": "Mensualidad Puerta de Hierro",
    "823": "Caza",

    # ── Grupo 9: GASTOS FINANCIEROS ───────────────────────────────────────────
    "9":   "GASTOS FINANCIEROS",

    "90":  "GASTOS EFECTIVO",
    "901": "Pérdida de dinero en efectivo",

    "91":  "GASTOS SANTANDER",
    "911": "Gastos financieros cuenta 123",
    "912": "Gastos financieros tarjeta compartida",
    "919": "Otros gastos financieros Santander",

    "92":  "GASTOS REVOLUT",
    "921": "Gastos financieros Revolut",

    "93":  "GASTOS INVERSIONES",
    "931":  "Abante",
    "9311": "Decrecimiento posiciones Abante",
    "9312": "Comisiones Abante",
    "932":  "Gastos MyInvestor",
    "9321": "Decrecimiento posiciones MyInvestor",
    "9322": "Comisiones MyInvestor",
    "933":  "Axa Inversiones",

    "99":  "GASTOS CRIPTOMONEDAS",
    "991": "Pérdidas Bitcoin",
    "992": "Pérdidas Doge",

    # ── INGRESOS (alphanumeric codes) ─────────────────────────────────────────
    "OTR":   "Otros Ingresos",
    "ABN":   "Incremento posiciones Abante",
    "EB":    "Extra pagos Bizum",
    "INVR":  "Ingresos realizados inversiones",
    "MYINV": "Incremento posiciones MyInvestor",
    "REV":   "Caja Fuerte Revolut",
    "SU-J":  "Sueldo Jaime",
    "SU-P":  "Sueldo Palo",
    "TR":    "Ingreso tipo Ticket Restaurante",
    "AXA":   "Axa inversiones",
}


def _is_leaf(code: str, plan: dict[str, str]) -> bool:
    """Returns True if no other key in plan starts with `code` followed by a digit."""
    return not any(
        other != code
        and other.startswith(code)
        and len(other) > len(code)
        and other[len(code)].isdigit()
        for other in plan
    )


# Leaf codes only — what the AI classifies transactions into
CATEGORIES: list[str] = [
    code for code in COSTS_PLAN if _is_leaf(code, COSTS_PLAN)
]


# ─── KEYWORD HINTS FOR FAST PRE-CLASSIFICATION ────────────────────────────────
# Maps lowercase text found in transaction description → leaf code in COSTS_PLAN.
# More specific entries must come before broader ones (dict is ordered).
KEYWORD_HINTS: dict[str, str] = {
    # Supermarkets
    "carrefour express": "442",
    "carrefour":         "441",
    "mercadona":         "441",
    "lidl":              "441",
    "aldi":              "441",
    "dia ":              "441",
    "eroski":            "441",
    "alcampo":           "441",
    "hipercor":          "441",
    "el corte ingles":   "441",

    # Eating out / delivery
    "glovo":             "501",
    "uber eats":         "501",
    "just eat":          "501",
    "deliveroo":         "501",

    # Transport
    "cabify":            "713",
    "uber":              "713",
    "bolt":              "713",
    "renfe":             "714",
    "metro":             "714",
    "emt ":              "714",
    "tmc ":              "714",

    # Subscriptions
    "netflix":           "432",
    "spotify":           "434",
    "hbo":               "435",
    "disney":            "435",
    "amazon prime":      "435",
    "apple.com/bill":    "431",

    # Bizum
    "bizum payment to":  "631",
    "bizum received from": "EB",

    # Salary
    "nomina":            "SU-J",
    "nómina":            "SU-J",
    "salario":           "SU-J",

    # Health
    "farmacia":          "801",
    "pharmacy":          "801",

    # Fuel
    "repsol":            "731",
    "bp ":               "731",
    "cepsa":             "731",
    "galp":              "731",
}
