# 💰 Categorizador de Gastos IA

Herramienta CLI en Python que lee exportaciones bancarias (CSV) y las categoriza automáticamente usando Claude AI.

## Instalación rápida

```bash
# 1. Clonar / descomprimir el proyecto
cd gastos-ia

# 2. Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar API Key
cp .env.example .env
# Editar .env y poner tu ANTHROPIC_API_KEY
# (obtener en https://console.anthropic.com)

# 5. Cargar variables de entorno
export $(cat .env | xargs)  # O usar python-dotenv
```

## Uso

```bash
# Modo interactivo (pregunta cuando tiene dudas)
python main.py data/ejemplo_movimientos.csv

# Modo automático (sin preguntas, usa mejor estimación)
python main.py data/mis_movimientos.csv --auto

# Especificar archivo de salida
python main.py data/movimientos_enero.csv -o resultados_enero.csv
```

## Funcionamiento

```
CSV banco → Leer → Categorizar → Exportar CSV listo para Google Sheets
                      │
                      ├── 1. Buscar en historial (sin API)
                      ├── 2. Keywords obvias (sin API)
                      ├── 3. Claude AI
                      └── 4. Preguntar usuario si hay duda
```

El historial se guarda en `data/historial.json`. Con el tiempo, el sistema aprende tus patrones y necesita llamar menos a la API.

## Personalización

Edita `categories.py` para:
- Ajustar tus categorías de gasto/ingreso
- Añadir tus cuentas bancarias
- Añadir keywords para clasificación rápida

## Roadmap

- [x] **Fase 1** — CLI local: CSV → categorización → export
- [ ] **Fase 2** — Google Sheets: subir resultados automáticamente
- [ ] **Fase 3** — Revolut API: obtener movimientos en tiempo real
- [ ] **Fase 4** — Telegram Bot: validar dudas por mensaje
- [ ] **Fase 5** — Dashboard: visualización de gastos

## Estructura

```
gastos-ia/
├── main.py           # Punto de entrada CLI
├── classifier.py     # Lógica de categorización con Claude
├── csv_reader.py     # Parser del CSV bancario
├── categories.py     # Tus categorías (personalizar aquí)
├── requirements.txt
├── .env.example      # Plantilla de variables de entorno
└── data/
    ├── ejemplo_movimientos.csv   # CSV de prueba
    └── historial.json            # Se crea automáticamente
```
