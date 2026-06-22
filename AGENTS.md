# AGENTS.md

## Objetivo

Mantener la plataforma Telco Churn reproducible en Databricks y publicable como evidencia técnica estática.

## Reglas

- No presentar GitHub Pages como un Databricks activo: publica documentación, métricas y capturas verificadas.
- No duplicar el README; `index.md` lo reutiliza como fuente canónica.
- No versionar perfiles, tokens ni URLs privadas de workspace.
- Mantener coherentes `docs/portfolio_deployment.md` y `portfolio.json`.

## Verificación mínima

Validar el bundle en Databricks solo cuando existan credenciales de entorno; para la publicación, comprobar el workflow `pages.yml` y los enlaces a activos.
