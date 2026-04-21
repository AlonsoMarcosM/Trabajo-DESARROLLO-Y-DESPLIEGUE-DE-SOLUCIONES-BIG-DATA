# Codigo - Guia completa de ejecucion (CLI y UI)

Esta carpeta contiene la implementacion tecnica de los hitos 2 y 3:

- Databricks Asset Bundle (`databricks.yml` + `resources/`)
- pipeline Medallion (`bronze`, `silver`, `gold`)
- notebooks de modelado y produccion ML (`05`, `07`, `08`)
- job de orquestacion de Hito 3 (`telco_churn_ml_orchestration`)
- generador de datos sinteticos masivo (`generate.py`)

El objetivo de esta guia es que cualquier persona del equipo pueda replicar
el flujo completo, de inicio a fin, sin depender de conocimiento previo.

## 1. Estructura relevante

```text
codigo/
|-- databricks.yml
|-- resources/
|   |-- telco_churn.job.yml
|   `-- telco_churn.pipeline.yml
|-- notebooks/
|   |-- 04_Feature_Store_Registration.py
|   |-- 05_Training_Dataset_Generation.ipynb
|   |-- 07_Training_Job.ipynb
|   |-- 07_Evaluation_Job.ipynb
|   |-- 07_MLflow_Experimentation.ipynb
|   |-- 07_Utils.py
|   |-- 08_Production.ipynb
|   `-- 08_Utils.py
`-- src/medallion_pipeline/
    |-- rules/
    |   |-- __init__.py
    |   `-- customers.py
    |-- transformations/
    |   |-- 01_bronze_ingestion.py
    |   |-- 02_silver_transformation.py
    |   |-- 03_gold_churn_spine.py
    |   |-- 03_gold_customer_profile.py
    |   `-- 03_gold_customer_aggregations.py
    |-- utilities/
    |   `-- generate.py
    `-- README.md
```

## 2. Requisitos previos

- Python instalado.
- Databricks CLI instalado (`databricks -v` debe funcionar).
- Permisos en el workspace para:
  - crear/ejecutar pipelines,
  - leer/escribir en Unity Catalog y Volumes.
- Recomendado:
  - tener autenticacion hecha con perfil propio (`databricks auth login`)
  - ejecutar todos los comandos desde la carpeta `codigo/`

## 3. Configuracion del bundle

### 3.1 Que define cada fichero

- `databricks.yml`
  - nombre del bundle.
  - target `dev`.
  - host del workspace de destino.
  - variables:
    - `uc_catalog`
    - `uc_schema`
    - `landing_volume_path`
- `resources/telco_churn.pipeline.yml`
  - recurso pipeline `telco_churn`.
  - librerias Python de transformacion (`01/02/03`).
- `resources/telco_churn.job.yml`
  - job de Hito 2 (`telco_churn_orchestration`).
  - job de Hito 3 (`telco_churn_ml_orchestration`).

### 3.2 Donde se configuran `var.uc_*`

1. Defaults en `databricks.yml` (bloque `variables`).
2. Uso en `resources/telco_churn.pipeline.yml` con `${var.uc_catalog}`, `${var.uc_schema}`, `${var.landing_volume_path}`.
3. Override en CLI con `--var` cuando sea necesario.

Ejemplo de override:

```powershell
databricks bundle validate -t dev -p <perfil> --var "uc_catalog=workspace,uc_schema=telco_churn,landing_volume_path=/Volumes/workspace/telco_churn/landing_zone"
```

### 3.3 Crear esquema y volume recomendados (CLI)

```powershell
databricks schemas create workspace.telco_churn --comment "Schema del proyecto Telco Churn para Hito 2 (pipeline medallion: bronze, silver y gold)." -p <perfil_databricks>
databricks volumes create workspace.telco_churn.landing_zone --volume-type MANAGED --comment "Landing zone del proyecto Telco Churn (context, events, source_buffer)." -p <perfil_databricks>
```

## 4. Flujo completo desde CLI (inicio a fin)

Ejecutar desde `codigo/`.

### 4.1 Login y perfil

```powershell
databricks auth login --host <workspace_host>

databricks auth login --host https://dbc-5ae029e2-ed3d.cloud.databricks.com

databricks auth profiles
```

### 4.2 Validar y desplegar bundle

```powershell
databricks bundle validate -t dev -p <perfil_databricks>
databricks bundle deploy -t dev -p <perfil_databricks>
```

Si el recurso estaba ligado a otro workspace:

```powershell
databricks bundle deployment unbind telco_churn -t dev -p <perfil_databricks>
databricks bundle deploy -t dev -p <perfil_databricks>
```

### 4.3 Generar datos reales (sin smoke test)

```powershell
cd src/medallion_pipeline/utilities
python -u generate.py *> generate_full.log
cd ../../..
```

Resultado esperado:

- dataset completo 2023-01 a 2025-06.
- salidas en:
  - `src/medallion_pipeline/utilities/context/`
  - `src/medallion_pipeline/utilities/events/`
  - `src/medallion_pipeline/utilities/source_buffer/`
- resumen en `src/medallion_pipeline/utilities/generate_full.log`.

### 4.4 Cargar datos al volume de Databricks

Nota: usa siempre el mismo `landing_volume_path` del pipeline.

```powershell
# Limpieza recomendada antes de recargar dataset completo
databricks fs rm "<landing_volume_path>/context" -r -p <perfil_databricks>
databricks fs rm "<landing_volume_path>/events" -r -p <perfil_databricks>
databricks fs rm "<landing_volume_path>/source_buffer" -r -p <perfil_databricks>

# Estructura minima
databricks fs mkdir "<landing_volume_path>/context" -p <perfil_databricks>
databricks fs mkdir "<landing_volume_path>/events" -p <perfil_databricks>
databricks fs mkdir "<landing_volume_path>/source_buffer" -p <perfil_databricks>

# Contexto
databricks fs cp "src/medallion_pipeline/utilities/context/customers.csv" "<landing_volume_path>/context/customers.csv" --overwrite -p <perfil_databricks>

# Eventos
databricks fs cp "src/medallion_pipeline/utilities/events/usage" "<landing_volume_path>/events/usage" -r --overwrite -p <perfil_databricks>
databricks fs cp "src/medallion_pipeline/utilities/events/labels" "<landing_volume_path>/events/labels" -r --overwrite -p <perfil_databricks>
databricks fs cp "src/medallion_pipeline/utilities/events/interactions" "<landing_volume_path>/events/interactions" -r --overwrite -p <perfil_databricks>

# Opcional (buffer 2025)
databricks fs cp "src/medallion_pipeline/utilities/source_buffer" "<landing_volume_path>/source_buffer" -r --overwrite -p <perfil_databricks>
```

### 4.5 Ejecutar pipeline

```powershell
databricks bundle run telco_churn -t dev -p <perfil_databricks>
```

Si cambiaste mucho volumen o esquema, usar full refresh:

```powershell
databricks bundle run telco_churn -t dev -p <perfil_databricks> --full-refresh-all
```

### 4.6 Ejecutar job final (pipeline -> notebook)

El bundle define un job final de orquestacion con dos tareas:

1. `run_telco_pipeline`
2. `run_feature_store_registration_simulation` (depende de la 1)

Ejecucion:

```powershell
databricks bundle run telco_churn_orchestration -t dev -p <perfil_databricks>
```

Notificaciones configuradas:

- `on_failure`: correos del equipo.
- `on_success`: correos del equipo.

### 4.7 Validar ejecucion (CLI) con checks rapidos

Comprobar recursos de gobierno:

```powershell
databricks catalogs get workspace -p <perfil_databricks>
databricks schemas get workspace.telco_churn -p <perfil_databricks>
databricks volumes read workspace.telco_churn.landing_zone -p <perfil_databricks>
```

Comprobar tablas del esquema:

```powershell
databricks tables list workspace telco_churn --max-results 200 -p <perfil_databricks>
```

Comprobar ultimo update de pipeline:

```powershell
databricks pipelines list-updates <pipeline_id> --max-results 5 -p <perfil_databricks>
```

Comprobar ultimo run de job:

```powershell
databricks jobs list-runs --job-id 992681729800259 --limit 5 -p <perfil_databricks>
```

## 5. Flujo equivalente desde UI de Databricks

## 5.1 Preparar catalog/schema/volume

1. Ir a `Catalog`.
2. Seleccionar catalog y schema objetivo.
3. Crear volumen (si no existe) para `landing_volume_path`.
4. Verificar que la ruta final coincida con la configurada en pipeline.

## 5.2 Cargar datos en el volume

1. En `Catalog`, abrir el volume.
2. Crear carpetas `context` y `events`.
3. Subir:
  - `context/customers.csv`
  - `events/usage/...`
  - `events/labels/...`
  - `events/interactions/...`
4. Opcional: subir `source_buffer/...`.

## 5.3 Crear o ejecutar pipeline desde UI

Si ya esta desplegada por bundle:

1. Ir a `Jobs & Pipelines`.
2. Buscar `Telco Churn - Hito 2 Medallion ETL`.
3. Abrir y pulsar `Start` o `Run update`.

## 5.4 Crear/ejecutar el job desde UI

Si ya esta desplegado por bundle:

1. Ir a `Jobs & Pipelines` -> `Jobs`.
2. Abrir `Telco Churn - Hito 2 Orchestration`.
3. Verificar que la tarea 2 depende de la tarea 1.
4. Revisar notificaciones (`on_success`/`on_failure`).
5. Pulsar `Run now`.
6. Confirmar en la vista del run:
  - tarea `run_telco_pipeline` en `SUCCESS`
  - tarea `run_feature_store_registration_simulation` en `SUCCESS`

Si quieres crear pipeline manual:

1. `Jobs & Pipelines` -> `Create pipeline`.
2. Configurar:
  - catalog.
  - schema.
  - development mode.
3. Anadir source files:
  - `src/medallion_pipeline/transformations/01_bronze_ingestion.py`
  - `src/medallion_pipeline/transformations/02_silver_transformation.py`
  - `src/medallion_pipeline/transformations/03_gold_churn_spine.py`
  - `src/medallion_pipeline/transformations/03_gold_customer_profile.py`
  - `src/medallion_pipeline/transformations/03_gold_customer_aggregations.py`
4. En `Configuration` definir `landing_volume_path`.
5. Guardar y ejecutar.

## 6. Validacion funcional (SQL)

Ejecutar en SQL Editor o notebook SQL:

```sql
SELECT COUNT(*) AS n FROM workspace.telco_churn.bronze_customers;
SELECT COUNT(*) AS n FROM workspace.telco_churn.bronze_usage;
SELECT COUNT(*) AS n FROM workspace.telco_churn.bronze_labels;
SELECT COUNT(*) AS n FROM workspace.telco_churn.bronze_interactions;

SELECT COUNT(*) AS n FROM workspace.telco_churn.silver_customers_history;
SELECT COUNT(*) AS n FROM workspace.telco_churn.silver_churn_events;
SELECT COUNT(*) AS n FROM workspace.telco_churn.silver_interactions_clean;
SELECT COUNT(*) AS n FROM workspace.telco_churn.silver_quarantine_customers;
SELECT COUNT(*) AS n FROM workspace.telco_churn.silver_quarantine_usage;
SELECT COUNT(*) AS n FROM workspace.telco_churn.silver_quarantine_labels;
SELECT COUNT(*) AS n FROM workspace.telco_churn.silver_quarantine_interactions;

SELECT COUNT(*) AS n FROM workspace.telco_churn.gold_churn_spine;
SELECT COUNT(*) AS n FROM workspace.telco_churn.gold_customer_profile;
SELECT COUNT(*) AS n FROM workspace.telco_churn.gold_customer_aggregations;
```

Comprobacion de ventanas temporales:

```sql
SELECT MIN(year_month) AS min_ym, MAX(year_month) AS max_ym
FROM workspace.telco_churn.gold_churn_spine;
```

Comprobacion de claves para Feature Store:

```sql
DESCRIBE TABLE EXTENDED workspace.telco_churn.gold_customer_profile;
DESCRIBE TABLE EXTENDED workspace.telco_churn.gold_customer_aggregations;
```

## 7. Errores tipicos y solucion

- `ImportError` en `rules`:
  - revisar imports y librerias en la definicion de pipeline.
- `QUOTA_EXCEEDED_EXCEPTION`:
  - hay otra update activa; esperar, cancelar o reintentar.
- `PATH_NOT_FOUND`:
  - la ruta de `landing_volume_path` no contiene la estructura esperada.
- cambio de workspace:
  - hacer `unbind` y redeploy del bundle.
- conflicto de esquema al recargar:
  - lanzar `databricks bundle run telco_churn -t dev --full-refresh-all`.

## 8. Que se sube a Git y que no

Se sube:

- codigo fuente,
- configuracion del bundle,
- documentacion.

No se sube:

- `codigo/.databricks/` (estado local del CLI),
- datos masivos generados por `generate.py`:
  - `src/medallion_pipeline/utilities/context/`
  - `src/medallion_pipeline/utilities/events/`
  - `src/medallion_pipeline/utilities/source_buffer/`
  - `src/medallion_pipeline/utilities/generate_full.log`

Motivo: son artefactos reproducibles, pesados y dependientes de entorno.

## 9. Replicacion para companero

Cada miembro del equipo debe:

1. clonar repo.
2. hacer `databricks auth login` con su usuario.
3. ejecutar `validate/deploy/run` con su perfil.
4. generar/cargar datos segun esta guia.

No hay que compartir `codigo/.databricks/bundle`; se regenera localmente.

## 10. Runbook para companero (desde cero)

### 10.1 Ruta CLI (recomendada para reproducibilidad)

1. Clonar repo y abrir terminal en `codigo/`.
2. Login con su usuario Databricks (`auth login`).
3. `bundle validate` y `bundle deploy`.
4. Generar datos (`generate.py`) y cargar al volumen.
5. Ejecutar pipeline (`bundle run telco_churn`).
6. Ejecutar job final (`bundle run telco_churn_orchestration`).
7. Validar tablas y estados con los checks de secciones 4.7 y 6.

### 10.2 Ruta UI (sin CLI para ejecucion)

1. Revisar catalogo/esquema/volumen en `Catalog`.
2. Subir datos al volumen en estructura correcta.
3. Ejecutar pipeline desde `Jobs & Pipelines`.
4. Ejecutar job de orquestacion desde `Jobs`.
5. Revisar tabla por tabla en `Catalog` y validar conteos en SQL Editor.

### 10.3 Criterio de "todo correcto"

Se considera que un companero ha replicado bien cuando:

1. Pipeline termina en `COMPLETED` sin `ERROR`.
2. Job termina en `SUCCESS` con ambas tareas en verde.
3. Existen tablas bronze/silver/gold en `workspace.telco_churn`.
4. El notebook `04_Feature_Store_Registration.py` finaliza en modo simulacion sin excepciones.
## 11. Regla para Hito 3 (train/test sin leakage temporal)

Para mantener coherencia con el enfoque del ejemplo del profesor y evitar fuga
de informacion entre entrenamiento y evaluacion:

- `events/*` se considera historico de entrenamiento (2023-2024).
- `source_buffer/*` se considera bloque de produccion/drift (2025 holdout).

Implicaciones practicas:

- Si entrenas para Hito 3, no mezclar 2025 con train.
- Reservar 2025 para validacion temporal final o simulacion de produccion.
- Si se decide ingerir 2025 en Bronze/Gold, etiquetar por periodo y mantener
  split temporal explicito en notebooks de modelado.

Comprobacion recomendada antes de entrenar:

```sql
SELECT MIN(year_month) AS min_ym, MAX(year_month) AS max_ym
FROM workspace.telco_churn.gold_churn_spine;
```

## 12. Ejecucion del job de Hito 3

La guia del proyecto separa el modelado del pipeline declarativo Medallion. Por eso los notebooks de Hito 3 no se incluyen como librerias en `resources/telco_churn.pipeline.yml`; se ejecutan mediante el job `telco_churn_ml_orchestration`.

Ejecutar desde `codigo/`:

```powershell
databricks bundle validate -t dev -p <perfil_databricks>
databricks bundle deploy -t dev -p <perfil_databricks>
databricks bundle run telco_churn_ml_orchestration -t dev -p <perfil_databricks>
```

Tareas del job:

1. `run_training_dataset_generation`: crea `workspace.telco_churn.gold_churn_training_dataset`.
2. `run_mlflow_experimentation`: ejecuta el grid search y registra el mejor modelo como `candidate`.
3. `run_production`: evalua champion/challenger y actualiza aliases en Unity Catalog.

Ultima ejecucion end-to-end validada:

- job id: `588950994995073`
- run id: `329240873651157`
- estado: `SUCCESS`
- modelo UC: `workspace.telco_churn.churn_lr_pipeline`
- alias final: `champion` en version 2; `rejected` en version 3.

## 13. Validacion funcional Hito 3

Comprobar tabla de entrenamiento:

```sql
SELECT COUNT(*) AS total_rows,
       SUM(CASE WHEN label_will_churn = 1 THEN 1 ELSE 0 END) AS churn_rows,
       SUM(CASE WHEN label_will_churn = 0 THEN 1 ELSE 0 END) AS retained_rows,
       MIN(usage_event_time) AS min_event_time,
       MAX(usage_event_time) AS max_event_time
FROM workspace.telco_churn.gold_churn_training_dataset;
```

Comprobar baseline de produccion:

```sql
SELECT COUNT(*) AS baseline_rows,
       MIN(usage_event_time) AS min_event_time,
       MAX(usage_event_time) AS max_event_time
FROM workspace.telco_churn.gold_churn_test_baseline;
```

Comprobar modelo registrado:

```powershell
databricks registered-models get workspace.telco_churn.churn_lr_pipeline --include-aliases -p <perfil_databricks>
databricks model-versions get-by-alias workspace.telco_churn.churn_lr_pipeline champion --include-aliases -p <perfil_databricks>
```

## 14. Documentacion relacionada

- Pipeline interno: `src/medallion_pipeline/README.md`
- Memoria Hito 2: `../documentacion/hito_2/memoria_hito_2.md`
- Memoria Hito 3: `../documentacion/hito_3/memoria_hito_3.md`
- Changelog tecnico: `CHANGELOG.md`
