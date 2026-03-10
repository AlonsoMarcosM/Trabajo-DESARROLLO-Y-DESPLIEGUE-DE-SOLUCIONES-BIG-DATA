# Changelog tecnico (codigo)

Este documento resume los cambios funcionales y el estado tecnico del proyecto
en Databricks, centrado en la carpeta `codigo/`.

## 2026-03-11 - Estado consolidado Hito 2

### Resumen ejecutivo

- Pipeline operativo en workspace objetivo (`dbc-5ae029e2-ed3d`).
- Bundle desplegado y update completa con `full refresh`.
- Datos masivos generados localmente y cargados en Unity Catalog Volume.
- Capas `bronze`, `silver`, `gold` materializadas en `workspace.default`.

### Evidencia tecnica (workspace objetivo)

- `pipeline_id`: `e9417948-9ced-41ae-a21a-8fcfd9994e37`
- Update `COMPLETED`: `bd86df0d-af54-4bf5-b935-9f6c6a477aa9` (2026-03-10)
- `landing_volume_path`: `/Volumes/workspace/default/landing_zone`

### Datos generados con `generate.py` (local)

- Total customers: `3,050,000`
- Total usage rows: `36,896,754`
- Total interactions: `19,379,826`
- Tamano aproximado:
  - `utilities/context`: `0.40 GB`
  - `utilities/events`: `17.22 GB`
  - `utilities/source_buffer`: `2.61 GB`

### Datos cargados y procesados en pipeline (workspace)

- Conteos actuales en tablas:
  - `bronze_customers`: `3,050,000`
  - `bronze_usage`: `32,121,558`
  - `bronze_labels`: `32,121,558`
  - `bronze_interactions`: `17,021,772`
  - `silver_usage_with_labels_batch`: `32,121,558`
  - `gold_churn_features`: `32,121,558`
  - `gold_churn_training_dataset`: `32,121,558`
- Quarantine:
  - `silver_customers_quarantine`: `0`
  - `silver_usage_quarantine`: `0`
  - `silver_labels_quarantine`: `0`
  - `silver_interactions_quarantine`: `0`

### Rango temporal actualmente ingerido

- `bronze_usage`, `bronze_labels`, `silver_usage`, `gold_churn_features`:
  - `min(year_month)=2023-01`
  - `max(year_month)=2024-12`

Nota:

- El generador escribe parte de 2025 en `utilities/source_buffer`.
- Esa rama (`source_buffer`) esta subida al Volume, pero no esta consumida por
  el script de ingestion actual (`01_bronze_ingestion.py`), que lee `events/*`.

Decision metodologica para Hito 3:

- mantener `2023-2024` como bloque de entrenamiento.
- mantener `2025` como bloque holdout de drift/produccion para test temporal.
- no mezclar ambos periodos durante ajuste del modelo para evitar leakage.

### Cambios de codigo y configuracion relevantes

- `databricks.yml`
  - host actualizado al workspace objetivo.
  - `sync.exclude` para no subir artefactos masivos generados localmente.
- `resources/telco_churn.pipeline.yml`
  - pipeline declarada con 3 librerias (`01_bronze`, `02_silver`, `03_gold`).
- `01_bronze_ingestion.py`
  - estabilizacion de esquema en `customer_updated_at` (cast a `string`).
- `02_silver_transformation.py`
  - fallback de reglas para evitar bloqueo por resolucion de imports en runtime.
- `03_gold_features.py`
  - capa gold activa para features y dataset de entrenamiento.
- `.gitignore`
  - exclusion de `codigo/.databricks/` y datos generados (`context`, `events`,
    `source_buffer`, `generate_full.log`).

### Incidencias registradas y resolucion

- `ImportError: attempted relative import with no known parent package`
  - causa: resolucion de imports relativa en runtime de pipeline.
  - accion: ajuste de estructura/imports y fallback de reglas en silver.
- `QUOTA_EXCEEDED_EXCEPTION` en workspace anterior (`dbc-8f4f...`)
  - causa: limite de pipelines activas en Free Edition.
  - accion: migracion operativa al workspace objetivo (`dbc-5ae...`).
- `413 Request Entity Too Large` durante deploy
  - causa: intento de sincronizar datos generados al bundle.
  - accion: exclusiones en `sync.exclude`.

## 2026-03-10 - Despliegue inicial y estabilizacion

- Login CLI y perfil operativo en workspace objetivo.
- Validacion y despliegue de bundle.
- Primera ejecucion del pipeline con incidencias de import/schema.
- Correcciones aplicadas y reintento con `full refresh`.
- Update final completada y tablas publicadas en `workspace.default`.

## Pendientes tecnicos (si se decide ampliar Hito 2)

- Incluir ingestion explicita de `source_buffer/2025` si se quiere que la capa
  gold contenga tambien 2025-01 a 2025-06 en esta fase.
- Formalizar versionado semantico de releases (`v0.1.0`, `v0.2.0`, etc.).
