# Documentacion del proyecto

Esta carpeta organiza la memoria tecnica del proyecto por hitos, manteniendo el enfoque incremental exigido por la asignatura.

## Estructura

- `fuentes/`: material de referencia (incluye la guia oficial del proyecto).
- `hito_1/`: version de memoria entregada para Hito 1.
- `hito_2/`: version incremental de memoria entregada para Hito 2.
- `hito_3/`: version incremental de memoria para Hito 3.
- `hito_4/`: version final incremental de memoria para Hito 4.

## Regla incremental de memoria

- Cada `memoria_hito_N` debe incluir:
  - todo el contenido de hitos anteriores,
  - el desarrollo completo del hito actual,
  - apartados reservados para hitos futuros si aun no estan completados.
- No crear memorias desconectadas por hito.
- Mantener continuidad narrativa entre entregas.

## Fuente de estructura obligatoria

- Referencia principal: `documentacion/fuentes/guia_proyecto.md`.
- La estructura minima esperada por hito se deriva de esa guia:
  - Hito 1: alcance, seleccion tecnica, viabilidad y planificacion.
  - Hito 2: entorno, gobernanza, bronze, silver, gold y verificacion.
  - Hito 3: modelado, experimentacion y evaluacion.
  - Hito 4: despliegue, monitorizacion y cierre.

## Estado validado Hito 3

- Memoria principal: `hito_3/memoria_hito_3.md`.
- Job validado: `telco_churn_ml_orchestration` (`run_id`: `329240873651157`, estado `SUCCESS`).
- Definicion del job: `../codigo/resources/telco_churn_ml.job.yml`.
- Modelo registrado: `workspace.telco_churn.churn_lr_pipeline`.
- Alias finales: `champion` version 2 y `rejected` version 3.
- Tabla baseline: `workspace.telco_churn.gold_churn_test_baseline`.
- Decision documentada: los notebooks de modelado no se insertan en `resources/telco_churn.pipeline.yml`; se orquestan por Job porque la guia separa Hito 3 del pipeline declarativo Medallion.

## Regla de formato

- Los archivos `.md` deben estar en Markdown real.
- Los archivos `.tex` se reservan para LaTeX.
- No mezclar sintaxis LaTeX estructural dentro de `.md`.
