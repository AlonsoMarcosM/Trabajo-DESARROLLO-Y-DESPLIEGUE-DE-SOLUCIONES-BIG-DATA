# Medallion Pipeline (Telco Churn)

Este directorio contiene la logica de preparacion de datos del Hito 2.

## Capas implementadas

- Bronze (`transformations/01_bronze_ingestion.py`)
  - Ingesta de `context/customers.csv` (batch).
  - Ingesta de `events/usage|labels|interactions` con Auto Loader (streaming).
  - Metadatos de auditoria: `ingestion_timestamp`, `source_file`.

- Silver (`transformations/02_silver_transformation.py`)
  - Reglas de calidad por entidad.
  - Cuarentena por tipo de dato (`silver_*_quarantine`).
  - Tablas limpias append-only (`silver_customers`, `silver_usage`, `silver_labels`, `silver_interactions`).
  - Join consolidado `silver_usage_with_labels_batch`.

- Gold (`transformations/03_gold_features.py`)
  - Feature table: `gold_churn_features`.
  - Dataset final de entrenamiento: `gold_churn_training_dataset`.

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
