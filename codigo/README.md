# Codigo - Guia de ejecucion reproducible

Esta carpeta contiene el codigo ejecutable del proyecto Telco Churn:

- Databricks Asset Bundle (`databricks.yml` y `resources/`).
- Pipeline Medallion de Hito 2.
- Notebooks y jobs de modelado de Hito 3.
- Simulacion, inferencia, enriquecimiento y monitorizacion de Hito 4.

Todos los comandos de esta guia se ejecutan desde `codigo/`, salvo que se indique lo contrario. Los valores entre `<...>` son placeholders que cada integrante debe sustituir por su perfil, job o recurso.

## 1. Requisitos previos

- Databricks CLI instalado.
- Perfil autenticado en el workspace:

```powershell
databricks auth login --host <workspace_host>
databricks auth profiles
```

- Permisos para ejecutar jobs, pipelines, consultar Unity Catalog y usar el SQL Warehouse del proyecto.
- Catalogo y esquema objetivo disponibles: `workspace.telco_churn`.
- Volumen UC de entrada configurado en el bundle mediante `landing_volume_path`.

## 2. Validar y desplegar el bundle

```powershell
databricks bundle validate -t dev -p <perfil_databricks>
databricks bundle deploy -t dev -p <perfil_databricks>
databricks bundle summary -t dev -p <perfil_databricks>
```

El `summary` muestra los IDs y URLs de los jobs y pipelines desplegados para el usuario que ejecuta el bundle.

## 3. Preparar datos

El generador reproducible es:

```powershell
python -u src/medallion_pipeline/utilities/generate.py
```

El generador crea salidas locales masivas. Esas salidas no se versionan en Git. Para cargarlas al volumen UC se puede usar la UI de Databricks o comandos `databricks fs cp` apuntando a las salidas generadas y al `<landing_volume_path>` configurado en el bundle.

Desde UI:

1. Abrir `Catalog`.
2. Entrar en `workspace.telco_churn`.
3. Abrir el volumen de entrada del proyecto.
4. Subir las salidas generadas manteniendo la estructura esperada por el pipeline.

Desde CLI, usar el patron:

```powershell
databricks fs cp "<ruta_salida_generada>" "<landing_volume_path>/<subruta_destino>" -r --overwrite -p <perfil_databricks>
```

## 4. Ejecutar Hito 2

Ejecutar solo el pipeline declarativo:

```powershell
databricks bundle run telco_churn -t dev -p <perfil_databricks>
```

Ejecutar la orquestacion diaria completa de datos:

```powershell
databricks bundle run telco_churn_orchestration -t dev -p <perfil_databricks>
```

Si se trabaja sobre el schema compartido `workspace.telco_churn`, debe usarse el pipeline que ya es propietario de las tablas. En la validacion de Hito 4 el propietario efectivo era el despliegue de Jose, por lo que la ejecucion replicable fue:

```powershell
databricks jobs run-now 304686448475692 -p <perfil_databricks>
databricks jobs get-run <run_id> -p <perfil_databricks>
```

El run validado fue `1053112867635794` y termino en `SUCCESS`.

## 5. Ejecutar Hito 3

El modelado no se ejecuta dentro del pipeline Medallion. Se lanza con el job `telco_churn_ml_orchestration`:

```powershell
databricks bundle run telco_churn_ml_orchestration -t dev -p <perfil_databricks>
```

Este job tiene tres tareas:

1. `run_training_dataset_generation`.
2. `run_mlflow_experimentation`.
3. `run_production`.

El ultimo run completo validado fue `329240873651157`, con modelo UC `workspace.telco_churn.churn_lr_pipeline`, alias `champion` en version 2 y alias `rejected` en version 3.

Comprobaciones rapidas sin relanzar entrenamiento:

```powershell
databricks jobs get-run 329240873651157 -p <perfil_databricks>
databricks registered-models get workspace.telco_churn.churn_lr_pipeline --include-aliases -p <perfil_databricks>
databricks model-versions get-by-alias workspace.telco_churn.churn_lr_pipeline champion --include-aliases -p <perfil_databricks>
```

## 6. Ejecutar Hito 4

### 6.1 Simulacion

Ejecutar el job de simulacion del bundle propio:

```powershell
databricks bundle run telco_churn_simulation -t dev -p <perfil_databricks>
```

Run validado en el despliegue de Alonso:

- Job ID: `134780552623506`
- Run ID: `1089331173774799`
- Estado: `SUCCESS`

### 6.2 Orquestacion diaria con inferencia

En el workspace compartido, el job validado de punta a punta fue el de Jose porque su pipeline es propietario de las tablas UC:

```powershell
databricks jobs run-now 304686448475692 -p <perfil_databricks>
databricks jobs get-run <run_id> -p <perfil_databricks>
```

Run validado:

- Job ID: `304686448475692`
- Run ID: `1053112867635794`
- Estado: `SUCCESS`
- Tareas en verde: `run_telco_pipeline`, `run_feature_store_registration_simulation`, `run_inference_and_label_enrichment`.

Si se quiere ejecutar desde UI:

1. Abrir `Jobs & Pipelines`.
2. Buscar `Telco Churn - Simulation` y pulsar `Run now`.
3. Buscar `Telco Churn - Hito 2 Orchestration` del propietario de las tablas y pulsar `Run now`.
4. Abrir el run y comprobar que todas las tareas terminan en `SUCCESS`.

## 7. Validacion funcional con SQL

Las siguientes consultas se pueden ejecutar en SQL Editor o desde cualquier notebook conectado al SQL Warehouse del proyecto.

Tabla de inferencia enriquecida:

```sql
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT customer_id) AS distinct_customers,
  MIN(year_month) AS min_month,
  MAX(year_month) AS max_month,
  SUM(CASE WHEN label_will_churn IS NOT NULL THEN 1 ELSE 0 END) AS labeled_rows,
  COUNT(DISTINCT model_version) AS model_versions
FROM workspace.telco_churn.gold_churn_inference_enriched;
```

Distribucion de predicciones:

```sql
SELECT
  model_version,
  prediction,
  COUNT(*) AS rows,
  AVG(prob_churn) AS avg_prob_churn,
  AVG(CAST(label_will_churn AS DOUBLE)) AS observed_churn_rate
FROM workspace.telco_churn.gold_churn_inference_enriched
GROUP BY model_version, prediction
ORDER BY model_version, prediction;
```

Metricas globales de monitorizacion:

```sql
WITH latest AS (
  SELECT MAX(window.start) AS max_window
  FROM workspace.telco_churn.gold_churn_inference_enriched_profile_metrics
)
SELECT
  CAST(window.start AS STRING) AS window_start,
  model_version,
  count AS row_count,
  accuracy_score,
  f1_score.weighted AS weighted_f1,
  precision.weighted AS weighted_precision,
  recall.weighted AS weighted_recall
FROM workspace.telco_churn.gold_churn_inference_enriched_profile_metrics
WHERE window.start = (SELECT max_window FROM latest)
  AND column_name = ':table'
  AND slice_key IS NULL
ORDER BY model_version;
```

Drift de variables de negocio:

```sql
WITH latest AS (
  SELECT MAX(window.start) AS max_window
  FROM workspace.telco_churn.gold_churn_inference_enriched_drift_metrics
)
SELECT column_name, js_distance
FROM workspace.telco_churn.gold_churn_inference_enriched_drift_metrics
WHERE window.start = (SELECT max_window FROM latest)
  AND column_name NOT IN (':table', 'year_month', 'customer_id', 'event_id',
                          'usage_event_time', 'inference_timestamp',
                          'label_event_time', 'model_version')
ORDER BY js_distance DESC
LIMIT 10;
```

## 8. Validacion de jobs y alertas

Listar jobs:

```powershell
databricks jobs list -p <perfil_databricks>
databricks jobs list-runs --job-id <job_id> --limit 5 -p <perfil_databricks>
```

Listar alertas:

```powershell
databricks alerts-v2 list-alerts -p <perfil_databricks>
```

Listar dashboards Lakeview:

```powershell
databricks lakeview list -p <perfil_databricks>
```

## 9. Regla de propiedad de tablas

Unity Catalog y Lakeflow no permiten que dos pipelines distintos gestionen la misma tabla materializada. Si el pipeline propio falla con un mensaje de tabla ya gestionada por otro pipeline, no se debe borrar ni recrear la tabla. La forma segura de reproducir la ejecucion compartida es lanzar el job del propietario efectivo o trabajar en un schema separado.

## 10. Documentacion relacionada

- Pipeline interno: `src/medallion_pipeline/README.md`
- Memoria Hito 4: `../documentacion/hito_4/memoria_hito_4.md`
- Changelog tecnico: `CHANGELOG.md`
