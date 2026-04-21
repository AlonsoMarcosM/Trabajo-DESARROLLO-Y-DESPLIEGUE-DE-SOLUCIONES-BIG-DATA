# Changelog tecnico (codigo)

Este documento resume los cambios funcionales y el estado tecnico del proyecto
en Databricks, centrado en la carpeta `codigo/`.

## 2026-04-22 - Cierre tecnico Hito 3 y orquestacion ML

### Resumen ejecutivo

- Implementado el ciclo de modelado de Hito 3 con notebooks independientes y job de Databricks.
- Separados los jobs por fichero de recurso, siguiendo la estructura recomendada por Databricks y el ejemplo del profesor:
  - `resources/telco_churn.job.yml`: job Hito 2.
  - `resources/telco_churn_ml.job.yml`: job Hito 3.
- Eliminado de `databricks.yml` el patron muerto `data_generator/` porque no existe en el repositorio y generaba warning.
- Mantenidas las exclusiones reales de artefactos masivos generados por `generate.py`.

### Estado validado (workspace objetivo)

- Job Hito 3: `[dev alonso_marcos] Telco Churn - Hito 3 ML Orchestration`
- Job id: `588950994995073`
- Run end-to-end validado en `SUCCESS`: `329240873651157`
- Modelo registrado: `workspace.telco_churn.churn_lr_pipeline`
- Alias finales:
  - `champion`: version 2
  - `rejected`: version 3
- Dataset de entrenamiento: `workspace.telco_churn.gold_churn_training_dataset`
  - filas: `16.316.445`
  - ventana: `2023-07-01` a `2024-12-01`
- Baseline de test: `workspace.telco_churn.gold_churn_test_baseline`
  - filas: `3.153.742`
  - ventana: `2024-10-01` a `2024-12-01`

### Como ejecutar Hito 3 desde CLI

Ejecutar desde `codigo/`:

```powershell
databricks bundle validate -t dev --profile alonso.marcos@alu.uclm.es
databricks bundle deploy -t dev --profile alonso.marcos@alu.uclm.es
databricks bundle run telco_churn_ml_orchestration -t dev --profile alonso.marcos@alu.uclm.es
```

El job ejecuta tres tareas secuenciales:

1. `run_training_dataset_generation`: genera `gold_churn_training_dataset`.
2. `run_mlflow_experimentation`: ejecuta grid search y registra el mejor candidato.
3. `run_production`: evalua champion/challenger y actualiza aliases en Unity Catalog.

### Como probar rapidamente el estado sin relanzar entrenamiento

Validar bundle:

```powershell
databricks bundle validate -t dev --profile alonso.marcos@alu.uclm.es
```

Comprobar el ultimo run validado:

```powershell
databricks jobs get-run 329240873651157 --profile alonso.marcos@alu.uclm.es
```

Comprobar modelo registrado:

```powershell
databricks registered-models get workspace.telco_churn.churn_lr_pipeline --include-aliases --profile alonso.marcos@alu.uclm.es
databricks model-versions get-by-alias workspace.telco_churn.churn_lr_pipeline champion --include-aliases --profile alonso.marcos@alu.uclm.es
```

Comprobar tablas desde SQL:

```sql
SELECT COUNT(*) AS total_rows,
       SUM(CASE WHEN label_will_churn = 1 THEN 1 ELSE 0 END) AS churn_rows,
       MIN(usage_event_time) AS min_event_time,
       MAX(usage_event_time) AS max_event_time
FROM workspace.telco_churn.gold_churn_training_dataset;

SELECT COUNT(*) AS baseline_rows,
       MIN(usage_event_time) AS min_event_time,
       MAX(usage_event_time) AS max_event_time
FROM workspace.telco_churn.gold_churn_test_baseline;
```

### Nota sobre reejecucion

- No hace falta relanzar el job de Hito 3 por separar `telco_churn_ml.job.yml`: solo cambia la organizacion del bundle, no la logica de tareas.
- Si se cambia el codigo de notebooks `05`, `07` u `08`, entonces si procede relanzar `telco_churn_ml_orchestration`.
- Si solo se actualizan documentos o comentarios YAML, basta con `bundle validate` y, si queremos reflejarlo en Databricks, `bundle deploy`.

## 2026-03-14 - Alineacion final Hito 2 y ejecucion completa

### Resumen ejecutivo

- Pipeline alineada a estructura del ejemplo del profesor (bronze/silver/gold por capas y ficheros separados).
- Migracion funcional a `workspace.telco_churn` (esquema dedicado con descripcion).
- Volume dedicado `workspace.telco_churn.landing_zone` con descripcion.
- Ejecucion `full refresh` completada en workspace objetivo.

### Estado validado (workspace objetivo)

- `pipeline_id`: `e9417948-9ced-41ae-a21a-8fcfd9994e37`
- Update `COMPLETED`: `aae8711c-6d5f-4502-b237-41f6b738c0e6` (2026-03-14)
- Catalog/esquema: `workspace.telco_churn`
- Volume de entrada: `/Volumes/workspace/telco_churn/landing_zone`
- Job orquestado Hito 2: `992681729800259`
- Run del job validada en `SUCCESS`: `640253146512278`

### Cambios de arquitectura aplicados

- `01_bronze_ingestion.py`
  - bronze en patron Medallion con `bronze_customers`, `bronze_usage`, `bronze_labels`, `bronze_interactions`.
- `02_silver_transformation.py`
  - cuarentenas por entidad.
  - historial SCD2 `silver_customers_history` con AUTO CDC.
  - ajuste de `silver_churn_events` a join stream-static para evitar sobrecarga de estado.
- Gold separada en 3 scripts:
  - `03_gold_churn_spine.py`
  - `03_gold_customer_profile.py`
  - `03_gold_customer_aggregations.py`

### Incidencias y mitigacion en esta iteracion

- `UNRESOLVED_COLUMN` por `_rescued_data` en AUTO CDC:
  - se elimino de `except_column_list` en clientes.
- `CANNOT_CHANGE_DATASET_TYPE` en `gold_customer_aggregations`:
  - se mantuvo tipo `STREAMING_TABLE` para compatibilidad del dataset existente.
- Ejecuciones largas con `OUT_OF_MEMORY` en joins de streams:
  - rediseño de joins en silver/gold para reducir estado y estabilizar update.

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
