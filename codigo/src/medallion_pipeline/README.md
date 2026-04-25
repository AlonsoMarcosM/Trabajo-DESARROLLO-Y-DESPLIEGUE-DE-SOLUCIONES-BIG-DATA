# Medallion Pipeline (Telco Churn)

Este directorio contiene la logica de preparacion de datos del Hito 2.
El modelado de Hito 3 no se ejecuta desde este pipeline declarativo; consume
las tablas gold mediante notebooks y el job `telco_churn_ml_orchestration`.

## Capas implementadas

- Bronze (`transformations/01_bronze_ingestion.py`)
  - Ingesta de `context/customers.csv` (batch).
  - Ingesta de `events/usage|labels|interactions` con Auto Loader (streaming).
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

## Ejecucion

Desde `codigo/`:

```powershell
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run telco_churn -t dev
```

## Prueba rapida para companero

Por CLI:

```powershell
databricks bundle run telco_churn -t dev
databricks bundle run telco_churn_orchestration -t dev
databricks bundle run telco_churn_ml_orchestration -t dev
```

Por UI:

1. Ejecutar pipeline `Telco Churn - Hito 2 Medallion ETL`.
2. Ejecutar job `Telco Churn - Hito 2 Orchestration`.
3. Verificar en `Catalog` que existen tablas bronze/silver/gold en `workspace.telco_churn`.
4. Para Hito 3, ejecutar job `Telco Churn - Hito 3 ML Orchestration` y verificar el modelo `workspace.telco_churn.churn_lr_pipeline`.
