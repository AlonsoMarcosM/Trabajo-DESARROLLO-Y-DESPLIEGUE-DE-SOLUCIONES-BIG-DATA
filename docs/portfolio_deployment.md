# Publicación documental

GitHub Pages expone la arquitectura, las métricas de producción simulada, las capturas de MLflow y Unity Catalog y la memoria del proyecto sin depender de un workspace Databricks activo.

El workflow `.github/workflows/pages.yml` construye el repositorio con Jekyll y publica `https://alonsomarcosm.github.io/Trabajo-DESARROLLO-Y-DESPLIEGUE-DE-SOLUCIONES-BIG-DATA/`.

La web no ejecuta pipelines ni modelos. La reproducción real continúa mediante Databricks Asset Bundles y los comandos documentados en `codigo/`.

Última verificación pública: 2026-06-22, respuesta HTTP 200 y workflow completo.
