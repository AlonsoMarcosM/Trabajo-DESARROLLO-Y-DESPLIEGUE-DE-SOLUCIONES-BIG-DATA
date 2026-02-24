# Estructura mínima de código

Esta carpeta está preparada para trabajar en Databricks con una base simple.

## Estructura

- `data_generator/generate.py`: script generador de datos proporcionado por el profesor.
- `databricks/notebooks/`: notebooks del proyecto.
- `databricks/pipelines/`: definiciones de pipelines (DLT u otros).
- `src/`: utilidades Python compartidas.

## Flujo recomendado

1. Ejecutar `data_generator/generate.py` para generar el dataset base.
2. Subir/ingestar esos datos en Databricks.
3. Desarrollar transformación y modelado en `databricks/notebooks/`.
4. Versionar cambios de notebooks y utilidades en este repositorio.
