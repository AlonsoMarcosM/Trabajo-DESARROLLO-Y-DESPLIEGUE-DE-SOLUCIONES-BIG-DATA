# Codigo del proyecto

Esta carpeta contiene el codigo fuente del proyecto con la misma estructura de directorios del ejemplo del profesor, pero sin reutilizar sus archivos.

## Estructura objetivo

- `.vscode/`
- `notebooks/`
- `resources/`
- `src/medallion_pipeline/`
  - `explorations/`
  - `rules/`
  - `transformations/`
  - `utilities/`

## Generacion de datos

Uno de los generadores de datos del proyecto es:

- `src/medallion_pipeline/utilities/generate.py`

Ese script crea datos sinteticos en las rutas `context/`, `events/` y `source_buffer/` en su carpeta de ejecucion.
