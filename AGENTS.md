# Working Preferences (Shared)

## Project context

- Asignatura: DESARROLLO Y DESPLIEGUE DE SOLUCIONES BIG DATA.
- Master: Master Universitario en Big Data y Computacion en la Nube.
- Curso: 2025-2026.
- Integrantes:
  - Alonso Marcos Munoz (`Alonso.Marcos@alu.uclm.es`)
  - Jose Barros Ribademar (`Jose.Barros1@alu.uclm.es`)

## Baseline from professor example

- Referencia: `Credit Card Fraud Detection Example Project`.
- Regla: replicar SOLO la estructura de directorios, no copiar archivos funcionales del ejemplo.
- Estructura requerida en `codigo/`:
  - `.vscode/`
  - `notebooks/`
  - `resources/`
  - `src/medallion_pipeline/explorations/`
  - `src/medallion_pipeline/rules/`
  - `src/medallion_pipeline/transformations/`
  - `src/medallion_pipeline/utilities/`

## Current codebase map

- Ruta principal de desarrollo: `Trabajo-DESARROLLO-Y-DESPLIEGUE-DE-SOLUCIONES-BIG-DATA/codigo`.
- `codigo` es un esqueleto vacio para implementar nuestro pipeline propio.
- No asumir que existen notebooks, pipelines o reglas preconstruidas: deben crearse para este proyecto.

## Data generation knowledge

- Generador confirmado del proyecto:
  - `codigo/src/medallion_pipeline/utilities/generate.py`
- El script genera un dataset sintetico de churn telco y escribe:
  - `context/customers.csv`
  - `events/usage/YYYY/MM/data.json`
  - `events/interactions/YYYY/MM/data.json`
  - `events/labels/YYYY/MM/data.json`
  - `source_buffer/...` para datos 2025 (simulacion de produccion)
- Ventana temporal de datos en el generador: 2023-01 a 2025-06, con drift de datos y de concepto en 2025.
- Importante:
  - `events/*` contiene el historico 2023-2024.
  - `source_buffer/*` contiene 2025 (produccion/drift) y NO entra automaticamente en bronze si solo se lee `events/*`.

## Databricks deployment knowledge (learned)

- Workspace operativo objetivo:
  - `https://dbc-5ae029e2-ed3d.cloud.databricks.com`
- Perfil CLI usado:
  - `alonso.marcos@alu.uclm.es`
- Pipeline bundle principal:
  - nombre: `telco_churn_etl`
  - id: `e9417948-9ced-41ae-a21a-8fcfd9994e37`
- Volume de entrada:
  - `/Volumes/workspace/default/landing_zone`
- Estado validado de update completa:
  - `update_id`: `bd86df0d-af54-4bf5-b935-9f6c6a477aa9`
  - `state`: `COMPLETED`

## Known incidents and fixes

- `ImportError: attempted relative import with no known parent package`
  - Causa: resolucion de imports en runtime de pipeline.
  - Mitigacion: imports robustos y fallback de reglas en silver.
- `QUOTA_EXCEEDED_EXCEPTION` (workspace free edition anterior)
  - Causa: limite de pipelines activas.
  - Mitigacion: trabajar en workspace propio objetivo.
- `413 Request Entity Too Large` durante `bundle deploy`
  - Causa: sync de datos locales masivos.
  - Mitigacion: excluir artefactos generados en `databricks.yml` (`sync.exclude`).

## Repo hygiene rules (critical)

- No versionar artefactos generados masivos:
  - `codigo/src/medallion_pipeline/utilities/context/`
  - `codigo/src/medallion_pipeline/utilities/events/`
  - `codigo/src/medallion_pipeline/utilities/source_buffer/`
  - `codigo/src/medallion_pipeline/utilities/generate_full.log`
- No versionar estado local de Databricks CLI:
  - `codigo/.databricks/`
- En documentacion del repo:
  - usar rutas relativas.
  - no usar rutas absolutas del sistema local.

## Delivery status conventions

- Hito 2 se considera cerrado si:
  - pipeline medallion desplegado y ejecutable end-to-end,
  - tablas bronze/silver/gold materializadas,
  - guia reproducible CLI/UI documentada.
- Si se exige incluir 2025 en gold:
  - mover/copiar `source_buffer/*` a `events/*` o ampliar ingestion bronze para leer `source_buffer/*`,
  - relanzar `full refresh`.

## Engineering conventions for this repo

- Mantener arquitectura Medallion (bronze/silver/gold) en `src/medallion_pipeline/transformations/`.
- Centralizar reglas de calidad en `src/medallion_pipeline/rules/`.
- Separar:
  - notebooks exploratorios en `notebooks/`
  - codigo productivo en `src/`
  - definiciones de despliegue en `resources/`
- Nombrado recomendado de transformaciones:
  - `01_bronze_*.py`
  - `02_silver_*.py`
  - `03_gold_*.py`

## Documentation style

- Redactar como estudiantes de master, con tono tecnico y natural.
- Evitar lenguaje de agente de IA o frases de plantilla.
- Priorizar sintesis y justificacion tecnica/economica.
