"""
Define aquí tus categorías de gastos e ingresos,
y las cuentas/cajas de activo que usas.

Personaliza estas listas según tu sistema en Google Sheets.
"""

# ─── CATEGORÍAS DE GASTO ──────────────────────────────────────────────────────
EXPENSE_CATEGORIES = [
    # Hogar
    "Alquiler",
    "Hipoteca",
    "Suministros (luz, agua, gas)",
    "Internet y móvil",
    "Hogar y limpieza",

    # Alimentación
    "Supermercado",
    "Restaurantes y bares",
    "Delivery (Glovo, Uber Eats)",

    # Transporte
    "Transporte público",
    "Gasolina",
    "Taxi / Cabify / Uber",
    "Parking",

    # Salud
    "Farmacia",
    "Médico / Seguro médico",
    "Gimnasio",

    # Ocio y cultura
    "Ocio y entretenimiento",
    "Streaming (Netflix, Spotify)",
    "Viajes y vacaciones",
    "Ropa y moda",

    # Finanzas
    "Ahorro / Inversión",
    "Seguros",
    "Impuestos y tasas",
    "Comisiones bancarias",

    # Social
    "Regalos",
    "Transferencias a personas",

    # Otros
    "Suscripciones",
    "Educación y formación",
    "Mascotas",
    "Sin categorizar",
]

# ─── CATEGORÍAS DE INGRESO ────────────────────────────────────────────────────
INCOME_CATEGORIES = [
    "Nómina / Salario",
    "Freelance / Factura",
    "Transferencia recibida",
    "Devolución",
    "Reembolso de seguro",
    "Ingreso extraordinario",
]

# ─── CUENTAS / CAJAS DE ACTIVO ────────────────────────────────────────────────
# Estas son las "cajas" de donde sale o entra el dinero en tu sistema
ASSET_ACCOUNTS = [
    "Actual",       # Tu cuenta principal
    "Revolut",
    "Efectivo",
    "Ahorro",
    # Añade aquí tus cuentas
]

# ─── UNIÓN DE TODAS LAS CATEGORÍAS ───────────────────────────────────────────
CATEGORIES = EXPENSE_CATEGORIES + INCOME_CATEGORIES


# ─── PALABRAS CLAVE PARA PRE-CLASIFICACIÓN RÁPIDA ────────────────────────────
# Ayuda a la IA y reduce llamadas a la API en casos obvios.
# Formato: "texto_en_descripcion_lowercase" -> "Categoría"
KEYWORD_HINTS = {
    # Supermercados
    "carrefour": "Supermercado",
    "mercadona": "Supermercado",
    "lidl": "Supermercado",
    "aldi": "Supermercado",
    "dia ": "Supermercado",
    "eroski": "Supermercado",
    "alcampo": "Supermercado",
    "hipercor": "Supermercado",
    "el corte ingles": "Supermercado",

    # Delivery
    "glovo": "Delivery (Glovo, Uber Eats)",
    "uber eats": "Delivery (Glovo, Uber Eats)",
    "just eat": "Delivery (Glovo, Uber Eats)",
    "deliveroo": "Delivery (Glovo, Uber Eats)",

    # Transporte
    "cabify": "Taxi / Cabify / Uber",
    "uber": "Taxi / Cabify / Uber",
    "bolt": "Taxi / Cabify / Uber",
    "renfe": "Transporte público",
    "metro": "Transporte público",
    "emt ": "Transporte público",
    "tmc ": "Transporte público",

    # Streaming
    "netflix": "Streaming (Netflix, Spotify)",
    "spotify": "Streaming (Netflix, Spotify)",
    "hbo": "Streaming (Netflix, Spotify)",
    "disney": "Streaming (Netflix, Spotify)",
    "amazon prime": "Streaming (Netflix, Spotify)",
    "apple.com/bill": "Suscripciones",

    # Bizum / transferencias
    "bizum payment to": "Transferencias a personas",
    "bizum received from": "Transferencia recibida",

    # Nómina
    "nomina": "Nómina / Salario",
    "nómina": "Nómina / Salario",
    "salario": "Nómina / Salario",

    # Farmacia
    "farmacia": "Farmacia",
    "pharmacy": "Farmacia",

    # Gasolina
    "repsol": "Gasolina",
    "bp ": "Gasolina",
    "cepsa": "Gasolina",
    "galp": "Gasolina",
}
