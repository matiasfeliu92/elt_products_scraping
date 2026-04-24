# ELT Products Scraping

Pipeline ELT para capturar precios y disponibilidad de productos de retail, conservar histórico y construir capas analíticas tipo medallón (`bronze` y `silver`) para seguimiento de cambios comerciales.

## 1. Descripción del proyecto

Este proyecto automatiza la extracción de datos de productos desde retailers de Argentina y su posterior procesamiento en capas de datos para análisis.

Flujo general:
1. Se lee un catálogo de productos desde Google Sheets.
2. Se hace scraping por producto/retailer con Selenium.
3. Se persiste la data cruda en MongoDB Atlas, evitando duplicados por precio.
4. Se exporta el snapshot diario a archivos JSON en Volumes (Databricks).
5. Se ingesta a una tabla Delta `bronze`.
6. Se transforma a una tabla Delta `silver` con calidad y métricas de descuento.

Retailers contemplados:
- Fravega
- Musimundo
- Megatone
- Naldo

---

## 2. Problemática y solución

### Problemática
Monitorear precios, stock y financiación en múltiples e-commerce suele ser un proceso manual, poco trazable y difícil de escalar. Además:
- Los sitios cambian estructura HTML con frecuencia.
- Los precios tienen formatos heterogéneos.
- Se requiere histórico para detectar cambios reales y evitar ruido.

### Solución implementada
El proyecto resuelve esto con:
- Scrapers por retailer con selectores dedicados.
- Manejo robusto de errores de scraping y trazabilidad en logs.
- Normalización de precios para comparar correctamente.
- Estrategia incremental: solo inserta en Mongo cuando hubo cambio de precio.
- Arquitectura medallón para pasar de datos crudos a datos analíticos listos para consumo.

---

## 3. Origen de los datos

### Fuente 1: Catálogo de productos
- Google Sheets (URL hardcodeada en `src/utils/google_sheet.py`).
- Campos esperados para el flujo: `product_id`, `retailer`, `link` (más atributos del catálogo).

### Fuente 2: Sitios web de retailers
- HTML público de páginas de producto.
- Extracción con Selenium + ChromeDriver en modo headless.

### Fuente 3: Persistencia operativa
- MongoDB Atlas (`db_name=products`), colecciones:
  - `scraped_products` (resultados de scraping)
  - `error_logs` (errores de extracción de elementos)

### Fuente 4: Capa lakehouse (Databricks)
- Export diario a JSON en `/Volumes/workspace/products/products_tracker/...`.
- Ingesta/transformación en tablas Delta (`bronze` y `silver`).

---

## 4. Arquitectura de datos

### 4.1 Etapas del proceso (en orden)
1. **Lectura de catálogo**
   - `main.py` + `src/utils/google_sheet.py`
   - Obtiene catálogo desde Google Sheets.
2. **Filtrado por retailer**
   - `src/scripts/extract_data.py`
   - Permite correr por tienda (`Fravega`, `Musimundo`, `Megatone`, `Naldo`) o total.
3. **Scraping por producto**
   - `src/scripts/scraping.py`
   - Usa selectores de `src/config/scraping_settings.py`.
4. **Normalización + carga incremental en MongoDB**
   - `src/scripts/load_data.py` + `src/utils/normalize_price.py`
   - Compara último precio guardado y evita insertar si no hay cambios.
5. **Registro de errores de scraping**
   - `src/utils/extract_elements.py` + `src/utils/load_errors.py`
   - Persistencia de excepciones por campo/producto en `error_logs`.
6. **Ingesta a capa Bronze (Databricks)**
   - `notebooks/01_data_ingestion.ipynb` (exporta JSON diario)
   - `notebooks/02_bronze_scraped_products.ipynb` (`COPY INTO` a Delta).
7. **Transformación a capa Silver (Databricks)**
   - `notebooks/03_silver_products.ipynb`
   - `MERGE` con catálogo, tipificación de precios y reglas de calidad.

### 4.2 Diagrama lógico

```text
Google Sheets (catalog)
        |
        v
  Python Orchestrator (Main)
        |
        v
 Selenium Scrapers por retailer
        |
        v
 MongoDB Atlas (scraped_products + error_logs)
        |
        v
 Databricks Volume (JSON diario)
        |
        v
 Delta Bronze (raw estructurada)
        |
        v
 Delta Silver (datos limpios + métricas)
```

---

## 5. Tecnologías usadas

### Lenguaje y librerías
- Python
- Selenium
- pandas
- gspread + google-auth
- pymongo
- python-dotenv
- webdriver-manager
- BeautifulSoup / lxml (dependencias disponibles)

### Plataforma y almacenamiento
- MongoDB Atlas
- Databricks (notebooks SQL/Python, Volumes)
- Delta Lake
- Google Sheets API

### Observabilidad
- Logging a consola y archivo (`logs/pipeline.log`).

---

## 6. Estructura del repositorio

```text
.
|-- main.py                        # Orquestador principal
|-- fravega.py                     # Entry point Fravega
|-- musimundo.py                   # Entry point Musimundo
|-- megatone.py                    # Entry point Megatone
|-- naldo.py                       # Entry point Naldo
|-- requirements.txt
|-- src/
|   |-- config/
|   |   |-- settings.py
|   |   |-- scraping_settings.py
|   |   |-- mongo_db.py
|   |   `-- logger.py
|   |-- scripts/
|   |   |-- extract_data.py
|   |   |-- scraping.py
|   |   `-- load_data.py
|   `-- utils/
|       |-- google_sheet.py
|       |-- extract_elements.py
|       |-- normalize_price.py
|       `-- load_errors.py
|-- notebooks/
|   |-- 01_data_ingestion.ipynb
|   |-- 02_bronze_scraped_products.ipynb
|   `-- 03_silver_products.ipynb
|-- queries/
|   |-- drafts.dbquery.ipynb
|   `-- medallon/
|       |-- bronze.dbquery.ipynb
|       `-- silver.dbquery.ipynb
|-- logs/
|   `-- pipeline.log
|-- data/                          # Actualmente vacía en este workspace
|-- dags/                          # Actualmente sin DAGs activos
`-- GCP_credentials/               # JSON de credenciales GCP
```

Nota: la carpeta `scraping/` contiene un entorno virtual local (venv) con dependencias instaladas.

---

## 7. Tablas y volúmenes

### 7.1 Entidades/tablas identificadas

#### MongoDB Atlas
- `products.scraped_products`
- `products.error_logs`

#### Databricks / Delta (medallón)
- `products.catalog`
- `workspace.products.bronze_scraped_products`
- `workspace.products.silver_products`

#### Tablas históricas/referenciadas en queries
- `products.raw_scrapping_data`
- `products.logs_errors_data`

Estas dos últimas aparecen en queries de diagnóstico y pueden corresponder a un esquema previo o alternativo del pipeline.

### 7.2 Columnas relevantes por capa

#### `products.catalog`
- `product_id`, `retailer`, `brand`, `main_category`, `sub_category`, `link`, etc.

#### `workspace.products.bronze_scraped_products`
- `scraped_at`, `product_id`, `retailer`, `sku`, `name`, `brand`
- `main_category`, `sub_category`
- `list_price`, `cash_price`, `stock`
- `installments_json`, `file_metadata_path`

#### `workspace.products.silver_products`
- `product_id`, `retailer`, `brand`, `name`
- `list_price` (DOUBLE), `cash_price` (DOUBLE)
- `scraped_at` (TIMESTAMP), `scraped_date` (DATE)
- `discount_pct`
- flags derivados: `is_available`, `is_valid_name`, `is_valid_price`, `discount_applied_str`, `discount_applied_int`

### 7.3 Volúmenes observados en este workspace
- `logs/pipeline.log`: **13.94 MB** (última escritura: 2026-04-24 12:50:44).
- `data/`: sin archivos actualmente.
- Ejecución registrada en logs:
  - `Total products loaded: 118` (catálogo leído)
  - `Total products to scrap: 28` (corrida filtrada por retailer)
- Comportamiento incremental observado: múltiples eventos `No hubo cambios en precios, no se inserta.`

### 7.4 Queries sugeridas para medir volumen en lakehouse

```sql
SELECT 'catalog' AS table_name, COUNT(*) FROM products.catalog
UNION ALL
SELECT 'bronze_scraped_products', COUNT(*) FROM products.bronze_scraped_products
UNION ALL
SELECT 'silver_products', COUNT(*) FROM products.silver_products;
```

---

## 8. Ejecución

## 8.1 Prerrequisitos
- Python 3.10+
- Google credentials JSON con acceso a la hoja de catálogo
- URI de MongoDB Atlas
- Chrome/Chromium disponible para Selenium

## 8.2 Variables de entorno
Basado en `.env.example`:

```env
GOOGLE_CREDENTIALS_PATH=GCP_credentials/tu_archivo.json
MONGO_DB_URI=mongodb+srv://...
```

Nota: en código también aparece la variable `GOOGLE_CREDENTIALS` en comentarios antiguos; la ruta efectiva usada por `Settings` se arma con `GOOGLE_CREDENTIALS_PATH`.

## 8.3 Instalación local

```bash
pip install -r requirements.txt
```

## 8.4 Ejecutar scraping por retailer

```bash
python fravega.py
python musimundo.py
python megatone.py
python naldo.py
```

## 8.5 Ejecutar scraping general desde `Main`
Si querés correr todos los retailers en una sola ejecución, instanciá `Main(retailer=None)`.

## 8.6 Flujo Databricks (medallón)
Ejecutar notebooks en orden:
1. `notebooks/01_data_ingestion.ipynb`
2. `notebooks/02_bronze_scraped_products.ipynb`
3. `notebooks/03_silver_products.ipynb`

## 8.7 Consultas de validación
Usar notebooks de `queries/` para:
- control de conteos por tabla,
- inspección de registros recientes,
- revisión de calidad y descuentos.

---

## 9. Observaciones y mejoras recomendadas

- `dags/` está sin DAGs activos: si se desea orquestación, formalizar DAGs de Airflow para scraping + medallón.
- Hay coexistencia de nombres de tablas (`raw_scrapping_data`/`logs_errors_data` vs `bronze/silver`): conviene unificar nomenclatura objetivo.
- Conviene excluir `scraping/` (venv) del control de versiones para reducir tamaño del repo.
- Se detectan `TimeoutException` en scraping (normal en sitios dinámicos): ajustar timeouts/retries por retailer puede mejorar cobertura.

---

## 10. Estado actual (snapshot)

- Pipeline Python activo y con logs actualizados al 2026-04-24.
- Carga incremental funcionando (evita inserciones sin cambios de precio).
- Arquitectura medallón implementada en notebooks Databricks.
- Carpeta `data/` local sin datasets persistidos en este workspace.
