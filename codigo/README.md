# Codigo - Guia completa de ejecucion (CLI y UI)

Esta carpeta contiene la implementacion tecnica del Hito 2:

- Databricks Asset Bundle (`databricks.yml` + `resources/`)
- pipeline Medallion (`bronze`, `silver`, `gold`)
- generador de datos sinteticos masivo (`generate.py`)

El objetivo de esta guia es que cualquier persona del equipo pueda replicar
el flujo completo, de inicio a fin, sin depender de conocimiento previo.

## 1. Estructura relevante

```text
codigo/
|-- databricks.yml
|-- resources/
|   `-- telco_churn.pipeline.yml
`-- src/medallion_pipeline/
    |-- rules/
    |   |-- __init__.py
    |   `-- customers.py
    |-- transformations/
    |   |-- 01_bronze_ingestion.py
    |   |-- 02_silver_transformation.py
    |   `-- 03_gold_features.py
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

### 3.2 Donde se configuran `var.uc_*`

1. Defaults en `databricks.yml` (bloque `variables`).
2. Uso en `resources/telco_churn.pipeline.yml` con `${var.uc_catalog}`, `${var.uc_schema}`, `${var.landing_volume_path}`.
3. Override en CLI con `--var` cuando sea necesario.

Ejemplo de override:

```powershell
databricks bundle validate -t dev -p <perfil> --var "uc_catalog=workspace,uc_schema=default,landing_volume_path=/Volumes/workspace/default/landing_zone"
```

## 4. Flujo completo desde CLI (inicio a fin)

Ejecutar desde `codigo/`.

### 4.1 Login y perfil

```powershell
databricks auth login --host <workspace_host>
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
databricks pipelines start-update <pipeline_id> --full-refresh -p <perfil_databricks>
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
2. Buscar `telco_churn_etl`.
3. Abrir y pulsar `Start` o `Run update`.

Si quieres crear pipeline manual:

1. `Jobs & Pipelines` -> `Create pipeline`.
2. Configurar:
  - catalog.
  - schema.
  - development mode.
3. Anadir source files:
  - `src/medallion_pipeline/transformations/01_bronze_ingestion.py`
  - `src/medallion_pipeline/transformations/02_silver_transformation.py`
  - `src/medallion_pipeline/transformations/03_gold_features.py`
4. En `Configuration` definir `landing_volume_path`.
5. Guardar y ejecutar.

## 6. Validacion funcional (SQL)

Ejecutar en SQL Editor o notebook SQL:

```sql
SELECT COUNT(*) AS n FROM workspace.default.bronze_customers;
SELECT COUNT(*) AS n FROM workspace.default.bronze_usage;
SELECT COUNT(*) AS n FROM workspace.default.bronze_labels;
SELECT COUNT(*) AS n FROM workspace.default.bronze_interactions;

SELECT COUNT(*) AS n FROM workspace.default.silver_customers;
SELECT COUNT(*) AS n FROM workspace.default.silver_usage;
SELECT COUNT(*) AS n FROM workspace.default.silver_labels;
SELECT COUNT(*) AS n FROM workspace.default.silver_interactions;
SELECT COUNT(*) AS n FROM workspace.default.silver_usage_with_labels_batch;

SELECT COUNT(*) AS n FROM workspace.default.gold_churn_features;
SELECT COUNT(*) AS n FROM workspace.default.gold_churn_training_dataset;
```

Comprobacion adicional recomendada:

```sql
SELECT
  SUM(CASE WHEN churn_date IS NOT NULL THEN 1 ELSE 0 END) AS churn_positive,
  COUNT(*) AS total_rows
FROM workspace.default.gold_churn_training_dataset;
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
  - lanzar `start-update --full-refresh`.

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

## 10. Regla para Hito 3 (train/test sin leakage temporal)

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
FROM workspace.default.gold_churn_features;
```

## 11. Documentacion relacionada

- Pipeline interno: `src/medallion_pipeline/README.md`
- Memoria Hito 2: `../documentacion/hito_2/memoria_hito_2.md`
- Changelog tecnico: `CHANGELOG.md`
