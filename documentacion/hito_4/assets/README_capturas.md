# Capturas pendientes para la memoria final

Guardar en esta carpeta capturas reales de Databricks con los nombres exactos indicados. La memoria `../memoria_hito_4.md` ya contiene las referencias textuales a cada una.

| Archivo esperado | Pantalla recomendada |
|---|---|
| `hito2_pipeline_medallion_dag.png` | Jobs & Pipelines > pipeline `[dev jose_barros1] Telco Churn - Hito 2 Medallion ETL`, con DAG de tablas y estado `COMPLETED`. |
| `hito3_mlflow_experiment_aucpr.png` | MLflow experiment `telco_churn_churn_detection_training`, con runs y métricas AUC-PR/AUC-ROC/F1. |
| `hito3_unity_catalog_model_aliases.png` | Unity Catalog > modelo `workspace.telco_churn.churn_lr_pipeline`, mostrando versiones y aliases `champion` y `rejected`. |
| `hito3_job_ml_success.png` | Jobs & Pipelines > run `329240873651157` del job `[dev alonso_marcos] Telco Churn - Hito 3 ML Orchestration`, con las tres tareas en `SUCCESS`. |
| `hito4_simulation_job_success.png` | Jobs & Pipelines > run `1089331173774799` del job `[dev alonso_marcos] Telco Churn - Simulation`, mostrando `SUCCESS` y `hours_to_inject = 1`. |
| `hito4_pipeline_propietario_updates.png` | Pipeline propietario `c69014f7-c33e-4919-afc4-454f9aabfc17`, con últimos updates `COMPLETED` y tablas de `workspace.telco_churn`. |
| `hito4_job_diario_run_success.png` | Run `1053112867635794` del job `[dev jose_barros1] Telco Churn - Hito 2 Orchestration`, con grafo de tareas en `SUCCESS`. |
| `hito4_inference_table_counts.png` | SQL Editor o Catalog Explorer con consulta/recuento de `workspace.telco_churn.gold_churn_inference_enriched`. |
| `hito4_lakehouse_monitor_dashboard.png` | Dashboard `gold_churn_inference_enriched Monitoring` o `Telco Churn Analytics Dashboard`; si aparece vacío, capturar tabla de métricas del monitor. |
| `hito4_alerts_ok.png` | Databricks SQL Alerts con `Alert ModelAcc_lt_085`, `Alert Drift_gt_005`, `Alert Completeness_lt_095` y `Alert zScore_gt_200` en `OK`. |

