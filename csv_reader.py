"""
Parser del CSV exportado del banco.
Soporta el formato de Revolut/Actual con columnas:
Tipo, Producto, Fecha de inicio, Fecha de finalización,
Descripción, Importe, Comisión, Divisa, State, Saldo
"""

import csv
from pathlib import Path
from datetime import datetime


def read_bank_csv(filepath: Path) -> list[dict]:
    """
    Lee el CSV del banco y devuelve lista de movimientos normalizados.
    
    Returns:
        Lista de dicts con claves: fecha, descripcion, importe,
        divisa, tipo, saldo, estado
    """
    movimientos = []

    # Intentar detectar el delimitador automáticamente
    with open(filepath, "r", encoding="utf-8-sig") as f:
        sample = f.read(2048)
    
    delimiter = ";" if sample.count(";") > sample.count(",") else ","

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        
        for i, row in enumerate(reader):
            try:
                mov = parse_row(row, i)
                if mov:
                    movimientos.append(mov)
            except Exception as e:
                print(f"⚠️  Fila {i+2} ignorada: {e} — {dict(row)}")

    # Ordenar por fecha descendente (más recientes primero)
    movimientos.sort(key=lambda x: x["fecha"], reverse=True)
    return movimientos


def parse_row(row: dict, index: int) -> dict | None:
    """Parsea una fila del CSV y devuelve dict normalizado."""
    
    # Normalizar nombres de columnas (quitar espacios, lowercase)
    row = {k.strip(): v.strip() if isinstance(v, str) else v for k, v in row.items()}

    # Descripción
    descripcion = (
        row.get("Descripción") or
        row.get("Descripcion") or
        row.get("Description") or
        row.get("Concepto") or
        ""
    ).strip()
    
    if not descripcion:
        return None  # Filas vacías o cabeceras duplicadas

    # Importe
    importe_raw = (
        row.get("Importe") or
        row.get("Amount") or
        row.get("Monto") or
        "0"
    )
    try:
        importe = float(str(importe_raw).replace(",", ".").replace(" ", ""))
    except ValueError:
        print(f"⚠️  Importe inválido: '{importe_raw}' en '{descripcion}'")
        importe = 0.0

    # Fecha
    fecha_raw = (
        row.get("Fecha de inicio") or
        row.get("Fecha") or
        row.get("Date") or
        row.get("Started Date") or
        ""
    )
    fecha = parse_date(fecha_raw)

    # Divisa
    divisa = row.get("Divisa") or row.get("Currency") or "EUR"

    # Tipo de operación
    tipo = row.get("Tipo") or row.get("Type") or ""

    # Estado
    estado = row.get("State") or row.get("Status") or "COMPLETADO"
    
    # Saltar transacciones pendientes/revertidas si se desea
    if estado.upper() in ("REVERTED", "DECLINED", "FAILED"):
        return None

    return {
        "id": index,
        "fecha": fecha,
        "descripcion": descripcion,
        "importe": importe,
        "divisa": divisa,
        "tipo": tipo,
        "estado": estado,
        "saldo": float(str(row.get("Saldo", "0") or row.get("Balance", "0")).replace(",", ".") or 0),
    }


def parse_date(fecha_raw: str) -> str:
    """Parsea fecha en varios formatos, devuelve YYYY-MM-DD."""
    if not fecha_raw:
        return ""
    
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%Y-%m-%dT%H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(fecha_raw.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # Si no parsea, devolver tal cual
    return fecha_raw.strip()
