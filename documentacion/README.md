# Documentación del proyecto

Esta carpeta contiene la memoria técnica incremental del proyecto y los recursos gráficos asociados.

## Estructura

```text
documentacion/
├── assets/                         — capturas de pantalla referenciadas en la memoria
│   ├── hito2_pipeline_medallion_dag.png
│   ├── hito3_mlflow_experiment_aucpr.png
│   ├── hito3_unity_catalog_model_aliases.png
│   ├── hito3_job_ml_success.png
│   ├── hito4_simulation_job_success.png
│   ├── hito4_pipeline_propietario_updates.png
│   ├── hito4_job_diario_run_success.png
│   ├── hito4_inference_table_counts.png
│   ├── hito4_lakehouse_monitor_dashboard.png
│   └── hito4_alerts_ok.png
├── memoria.md                      — memoria técnica incremental completa (Hitos 1-4)
├── memoria.pdf                     — versión PDF para entrega
├── memoria.tex                     — fuente LaTeX
└── README.md
```

Las carpetas `fuentes/`, `hito_1/`, `hito_2/` y `hito_3/` existen en local pero están excluidas del repositorio remoto (`.gitignore`).

## Documento principal

`memoria.md` es la memoria técnica incremental única que cubre los cuatro hitos:

- **Hito 1**: alcance, selección técnica, viabilidad y planificación.
- **Hito 2**: entorno, gobernanza, Bronze, Silver, Gold y verificación.
- **Hito 3**: modelado, experimentación y evaluación.
- **Hito 4**: despliegue, monitorización y cierre.

Cada hito incorpora todo el contenido de los anteriores manteniendo continuidad narrativa.

## Regla incremental de memoria

- Cada versión incluye el desarrollo completo de todos los hitos hasta la fecha de entrega.
- No se crean memorias desconectadas por hito.
- La memoria se entrega también en PDF generado desde LaTeX (`memoria.tex`).

## Estado validado Hito 4

- Memoria principal: `memoria.md`.
- Job ML validado: `telco_churn_ml_orchestration` (estado `SUCCESS`).
- Modelo registrado: `workspace.telco_churn.churn_lr_pipeline`.
- Alias finales: `champion` versión 2, `rejected` versión 3.
- Tabla de inferencia enriquecida: `workspace.telco_churn.gold_churn_inference_enriched`.
- Monitorización activa: `gold_churn_inference_enriched_profile_metrics` y `drift_metrics`.
- Alertas configuradas: accuracy, drift, completitud y volumen.

## Regla de formato

- Los archivos `.md` están en Markdown estándar.
- Los archivos `.tex` se reservan para LaTeX.
- Las imágenes se referencian con rutas relativas desde `documentacion/`: `assets/nombre.png`.
