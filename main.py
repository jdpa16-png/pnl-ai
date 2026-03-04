#!/usr/bin/env python3
"""
Categorizador de gastos con IA - Fase 1
Lee un CSV bancario, categoriza automáticamente y exporta resultado.
"""

import argparse
import sys
from pathlib import Path

from csv_reader import read_bank_csv
from classifier import ExpenseClassifier
from categories import CATEGORIES, ASSET_ACCOUNTS


def main():
    parser = argparse.ArgumentParser(description="Categorizador de gastos con IA")
    parser.add_argument("csv_file", help="Ruta al CSV exportado del banco")
    parser.add_argument(
        "--output", "-o", default="movimientos_categorizados.csv",
        help="Archivo de salida (default: movimientos_categorizados.csv)"
    )
    parser.add_argument(
        "--historial", default="data/historial.json",
        help="Ruta al historial de categorizaciones previas"
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="Modo automático: no preguntar, usar mejor estimación siempre"
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"❌ Error: No se encuentra el archivo {csv_path}")
        sys.exit(1)

    print(f"\n💰 Categorizador de Gastos IA")
    print(f"{'='*50}")
    print(f"📂 Leyendo: {csv_path.name}")

    # 1. Leer CSV
    movimientos = read_bank_csv(csv_path)
    print(f"✅ {len(movimientos)} movimientos cargados\n")

    # 2. Clasificar
    classifier = ExpenseClassifier(
        historial_path=args.historial,
        interactive=not args.auto
    )
    
    resultados = classifier.classify_batch(movimientos)

    # 3. Exportar
    output_path = Path(args.output)
    export_results(resultados, output_path)

    # 4. Resumen
    print(f"\n{'='*50}")
    print(f"✅ Resultado guardado en: {output_path}")
    print_summary(resultados)


def export_results(resultados: list[dict], output_path: Path):
    """Exporta los resultados a CSV."""
    import csv
    
    fieldnames = [
        "Fecha", "Descripción", "Importe", "Divisa",
        "Categoría", "Cuenta_Origen", "Confianza", "Tipo"
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in resultados:
            writer.writerow({
                "Fecha": r.get("fecha", ""),
                "Descripción": r.get("descripcion", ""),
                "Importe": r.get("importe", ""),
                "Divisa": r.get("divisa", "EUR"),
                "Categoría": r.get("categoria", "Sin categorizar"),
                "Cuenta_Origen": r.get("cuenta_origen", "Actual"),
                "Confianza": r.get("confianza", ""),
                "Tipo": r.get("tipo", ""),
            })


def print_summary(resultados: list[dict]):
    """Imprime resumen de gastos por categoría."""
    from collections import defaultdict
    
    por_categoria = defaultdict(float)
    for r in resultados:
        if r.get("importe", 0) < 0:  # Solo gastos
            cat = r.get("categoria", "Sin categorizar")
            por_categoria[cat] += abs(r["importe"])
    
    print("\n📊 Resumen de gastos:")
    for cat, total in sorted(por_categoria.items(), key=lambda x: -x[1]):
        print(f"  {cat:<30} {total:>8.2f} EUR")
    
    total_gastos = sum(v for v in por_categoria.values())
    total_ingresos = sum(r["importe"] for r in resultados if r.get("importe", 0) > 0)
    print(f"\n  {'Total gastos':<30} {total_gastos:>8.2f} EUR")
    print(f"  {'Total ingresos':<30} {total_ingresos:>8.2f} EUR")
    print(f"  {'Balance':<30} {total_ingresos - total_gastos:>8.2f} EUR")


if __name__ == "__main__":
    main()
