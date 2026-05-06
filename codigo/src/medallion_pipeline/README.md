# Medallion Pipeline (Telco Churn)

Este directorio contiene la logica de preparacion de datos del Hito 2.
El modelado de Hito 3 no se ejecuta desde este pipeline declarativo; consume
las tablas gold mediante notebooks y el job `telco_churn_ml_orchestration`.
En Hito 4, la inferencia y el enriquecimiento de etiquetas se ejecutan desde
el job de orquestacion diario, despues de refrescar bronze, silver y gold.

## Capas implementadas

- Bronze (`transformations/01_bronze_ingestion.py`)
  - Ingesta batch del maestro de clientes generado.
  - Ingesta incremental de eventos mensuales de uso, etiquetas e interacciones con Auto Loader.
  - Metadatos de auditoria: `ingestion_timestamp`, `source_file`.

- Silver (`transformations/02_silver_transformation.py`)
  - Reglas de calidad por entidad y tablas de cuarentena:
    - `silver_quarantine_customers`
    - `silver_quarantine_usage`
    - `silver_quarantine_labels`
    - `silver_quarantine_interactions`
  - Historial SCD2 de clientes con AUTO CDC:
    - `silver_customers_history`
  - Join stream-static para eventos unificados (menos estado y mas estable):
    - `silver_churn_events`
  - Tabla limpia de interacciones:
    - `silver_interactions_clean`

- Gold
  - `transformations/03_gold_churn_spine.py`
    - `gold_churn_spine`
  - `transformations/03_gold_customer_profile.py`
    - `gold_customer_profile` (PK temporal para PiT)
  - `transformations/03_gold_customer_aggregations.py`
    - `gold_customer_aggregations` (features derivadas por cliente-mes)

## Reglas de calidad

Reglas declaradas en `rules/customers.py`:

- validacion de identificadores nulos.
- validacion de rangos numericos.
- validacion de dominio de `interaction_type`.

## Configuracion del pipeline

El recurso del pipeline se define en:

- `resources/telco_churn.pipeline.yml`

Variables recibidas desde bundle:

- `uc_catalog`
- `uc_schema`
- `landing_volume_path`

## Ejecucion reproducible

Desde `codigo/`:

```powershell
databricks bundle validate -t dev -p <perfil_databricks>
databricks bundle deploy -t dev -p <perfil_databricks>
databricks bundle run telco_churn -t dev -p <perfil_databricks>
```

Para ejecutar la orquestacion diaria completa de datos e inferencia:

```powershell
databricks bundle run telco_churn_orchestration -t dev -p <perfil_databricks>
```

En el workspace compartido, si las tablas ya pertenecen al pipeline desplegado
por otro integrante, hay que lanzar el job propietario de esas tablas. El run
validado de Hito 4 se reprodujo asi:

```powershell
databricks jobs run-now 304686448475692 -p <perfil_databricks>
databricks jobs get-run <run_id> -p <perfil_databricks>
```

Run validado: `1053112867635794`, estado `SUCCESS`.

## Prueba rapida para companero

Por CLI:

```powershell
databricks bundle run telco_churn -t dev -p <perfil_databricks>
databricks bundle run telco_churn_orchestration -t dev -p <perfil_databricks>
databricks bundle run telco_churn_ml_orchestration -t dev -p <perfil_databricks>
```

Por UI:

1. Ejecutar pipeline `Telco Churn - Hito 2 Medallion ETL`.
2. Ejecutar job `Telco Churn - Hito 2 Orchestration`.
3. Verificar en `Catalog` que existen tablas bronze/silver/gold en `workspace.telco_churn`.
4. Para Hito 3, ejecutar job `Telco Churn - Hito 3 ML Orchestration` y verificar el modelo `workspace.telco_churn.churn_lr_pipeline`.
5. Para Hito 4, ejecutar `Telco Churn - Simulation`, ejecutar despues el job diario propietario y comprobar la tabla `workspace.telco_churn.gold_churn_inference_enriched`.

## Validacion SQL de Hito 4

```sql
SELECT COUNT(*) AS total_rows,
       COUNT(DISTINCT customer_id) AS distinct_customers,
       MIN(year_month) AS min_month,
       MAX(year_month) AS max_month
FROM workspace.telco_churn.gold_churn_inference_enriched;
```

```sql
SELECT model_version,
       prediction,
       COUNT(*) AS rows,
       AVG(prob_churn) AS avg_prob_churn,
       AVG(CAST(label_will_churn AS DOUBLE)) AS observed_churn_rate
FROM workspace.telco_churn.gold_churn_inference_enriched
GROUP BY model_version, prediction
ORDER BY model_version, prediction;
```
