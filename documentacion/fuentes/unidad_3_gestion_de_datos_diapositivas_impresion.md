# unidad_3_gestion_de_datos_diapositivas_impresion

_Fuente original: `unidad_3_gestion_de_datos_diapositivas_impresion.pdf`_

## Pagina 1

Desarrollo y Despliegue de Soluciones Big Data Unidad 3: Gestión de datos Del dato crudo al activo de confianza Juan Carlos Alfaro Jiménez Máster Universitario en Big Data y Computación en la Nube

## Pagina 2

Unidad 3: Gestión de datos Contenido

## 1. Integridad y diseño del dato

## 2. Preprocesamiento de datos

## 3. Metadatos, esquemas y almacenamiento

## Pagina 3

El desafío de los datos en producción Datos estáticos contra datos dinámicos Datos estáticos Datos dinámicos Maximizar métrica de Inferencia rápida e rendimiento interpretabilidad Monitoreo y reentrenamiento Ajuste óptimo continuo Importante Crucial Algoritmo de máximo El sistema entero rendimiento Académico Producción 3

## Pagina 4

Arquitectura y flujo de datos Automatización y soluciones de diseño Ingesta Preparación Producción Monitorización Captura del dato Transformación y división Salida y generación de valor Disparador externo Validación Entrenamiento Orquestador Filtros de calidad Ejecución del modelo principal Director del flujo 4

## Pagina 5

Ingesta y validación Garantizando la calidad del dato desde el origen Fuentes de datos Proceso de validación Puerta de calidad Recopilación de datos Aplicación de reglas Detección y acción de fuentes en tiempo para validar dato sobre anomalías de real y estáticas datos 5

## Pagina 6

Preparación de datos Convirtiendo datos crudos en señales predictivas Estrategia de división Transformación de datos Consistencia del pipeline Dividir datos en Convertir datos crudos Asegurar transformaciones conjunto de en señales predictivas consistentes entre entrenamiento, entrenamiento y predicción validación y prueba 6

## Pagina 7

Monitorización y actualización El ciclo de vida continuo del dato Monitorizar datos Evaluar la salud y patrones de datos Desplegar actualización Detectar desviaciones Implementar el modelo mejorado Identificar anomalías en los datos Reentrenar modelo Activar alertas Actualizar el modelo con datos recientes Notificar sobre reglas obsoletas Reiniciar pipeline Iniciar el proceso de actualización 7

## Pagina 8

Responsabilidad en los datos Identificación y gestión sesgos sistémicos Lugar Contexto Importe Predicción Realidad Resultado Supermercado Local 45.00 Legítima Légitima Acierto Cafetería Habitual 12.00 Legítima Légitima Acierto Tienda artesanía Internacional 85.00 Fraude Legítima Error 8

## Pagina 9

Fuentes de información El origen de los datos en nuestro sistema Críticos Flujo en tiempo real y datos imperativos para inferencia Datos en producción Complementarios Datos sintéticos y extraídos de la Datos de web para contexto enriquecimiento Base de datos Datos Conjuntos de datos propios y de fundacionales código abierto 9

## Pagina 10

Seguridad y privacidad Protección de la información de identificación personal Mecanismos de protección Seguridad de datos Técnicas como la agregación y el Políticas y salvaguardas técnicas enmascaramiento para proteger la para prevenir fugas y identidad. vulnerabilidades. Privacidad de datos Cumplimiento normativo Gestión del ciclo de vida de los Adherencia estricta a las datos con transparencia y regulaciones de protección de datos. consentimiento del usuario. 10

## Pagina 11

El compromiso con la equidad Representación y mitigación de la amplificación de sesgos Datos históricos desequilibrados Falta de diversidad en los Amplificación de sesgos datos históricos. El modelo amplifica los sesgos existentes en los Paridad predictiva datos. La precisión del modelo es estable entre diferentes Igualdad predictiva grupos. El modelo castiga más a un Igualdad de grupo que a otro por error. oportunidades El modelo detecta la etiqueta correcta con la misma Paridad estadística eficacia para todos. Los resultados finales del modelo están equilibrados demográficamente. 11

## Pagina 12

Reducción del sesgo: el factor humano Tipos de clasificadores y gestión de la calidad Generalistas Usuarios finales Expertos Tareas sencillas, Fuente continua, Patrones complejos, bajo coste interacción directa alto coste 12

## Pagina 13

Desafíos finales en producción Mantenimiento de la integridad y rendimiento del sistema 1 2 Proteger Maximizar identidad utilidad Priorizar la privacidad Priorizar la utilidad de sobre la utilidad de los datos sobre la los datos. privacidad. 3 4 Sacrificar Maximizar precisión rendimiento Priorizar la equidad Priorizar el sobre el rendimiento rendimiento global global. sobre la equidad. 13

## Pagina 14

Problemas con modelos desplegados Identificación de la degradación del rendimiento Fallos silenciosos El modelo acepta peticiones con errores internos. Problemas graduales El mundo cambia y el modelo caduca. Fallos del sistema Errores técnicos súbitos como actualizaciones o caídas de red. 14

## Pagina 15

Cambios en datos y conceptos Velocidad en el entorno y estrategias de reentrenamiento Cambio lento Cambio medio Cambio rápido Reentreno por Feedback humano Automatización mejores técnicas para validación total inmediata 15

## Pagina 16

Detección de anomalías en los datos Diferencias fundamentales entre skew y drift Desconexión Cambio natural del inmediata mundo Observar Detección tendencias y automática fácil planificar Fallo inmediato Fallo silencioso Skew Drift 16

## Pagina 17

Detección de skew en los datos Variantes de esquema y distribución Balance operativo Filtro nivel 1 Establecer Detección de Reacción proactiva línea base schema skew antes del fallo (rompe reglas de masivo, pero con Filtro nivel 2 Perfil de salud de formato) y alerta alto coste los datos de Detección de técnica computacional entrenamiento distribution skew (esquema y (valores divergen) y estadísticas) análisis proactivo 1 2 3 4 Paso 1 Paso 2 Paso 3 Resultado 17

## Pagina 18

Detección de problemas en los datos Evolución de data y concept drift Concept drift Data drift El significado de los datos cambia, afectando la relación La distribución de las variables entre las variables de entrada y la de entrada cambia, pero la variable de salida. relación entre las variables de entrada y la variable de salida permanece igual. 18

## Pagina 19

Unidad 3: Gestión de datos Contenido

## 1. Integridad y diseño del dato

## 2. Preprocesamiento de datos

## 3. Metadatos, esquemas y almacenamiento

## Pagina 20

Fundamentos en el preprocesamiento de datos Maximizando el valor predictivo y la eficiencia de cómputo Establecer el Implementar objetivo metodología Definir la Iterativa transformación de Tomar datos de brutos a Añadir y ajustar decisiones optimizados características gradualmente Decidir si continuar o retroceder Aplicar la regla de oro Monitorizar Equilibrar resultados rendimiento y recursos de Evaluar mejoras y cómputo rentabilidad 20

## Pagina 21

Replicabilidad en el preprocesamiento de datos Sincronía entre entrenamiento e inferencia Potencial Exprimir al máximo la Training-serving Coordinación información para aprender. Entrenamiento Inferencia skew perfecta Eficiencia Lógica discrepa Congelar estadísticas Aplicar Lógica consistente entre fases globales constantes entre fases congeladas Mínimos atributos es menor coste de cómputo. Consistencia Ejecución idéntica en diseño y producción. 21

## Pagina 22

Arquitectura del flujo de preprocesamiento Flujo lógico desde el dato bruto al vector de características Mapeo y limpieza Corregir errores y convertir formatos brutos a numéricos. Construcción de características Generar atributos sintéticos y cruces de variables. Transformación y escalado Ajustar magnitudes numéricas para facilitar a convergencia del modelo. 1 Selección y reducción 2 Identificar el subconjunto más 3 valioso y eliminar redundancia. 4 22

## Pagina 23

Fase 1: mapeo y limpieza de datos Preparación de la estructura base del vector de características Limpieza de Mapeo de Gestión de datos tipos vocabularios Corregir Convertir datos a Mapear texto a inconsistencias y formatos identificadores eliminar anomalías numéricos enteros 23

## Pagina 24

Fase 2: construcción de características Capturando relaciones no lineales y atributos sintéticos Atributos sintéticos Operaciones matemáticas para extraer señales claras de los datos. Cruce de características Combinar variables para capturar interacciones no lineales. Consistencia Realizar la construcción de características antes del escalado para la consistencia. 24

## Pagina 25

Fase 3: transformación y escalado Homeogeneización y estabilidad numérica del vector de atributos Escalado Discretización Comprime datos a un Agrupa valores continuos rango fijo para evitar el en categorías para sesgo por magnitud. simplificar el análisis. Estandarización Desplaza la distribución para gestionar valores atípicos. 25

## Pagina 26

Fase 4: selección de características y reducción de la dimensionalidad Optimización del espacio de atributos para la eficiencia operativa Wrapper Reducción Precisa pero Filter Comprime computacionalme variables, pero nte costosa. Rápida y eficiente, Embedded puede perder pero puede omitir información. interacciones Integrado en el importantes. modelo, pero puede ser menos interpretable. 26

## Pagina 27

Preprocesamiento a escala de datos De la experimentación en libretas a la producción masiva Cientos de Terabytes de megabytes información Manual y Masivo y artesanal automatizado Cómodo y rápido Requisito Entorno experimental Entorno real 27

## Pagina 28

Estrategias para la consistencia y el despliegue Pipelines unificados y el riesgo del training-serving skew Training-serving skew Las transformaciones no son espejos exactos Despliegue multi-entorno Despliegue en nube, edge y web Validación de datos Validar con subconjunto Traducción de datos. manual Evitar la traducción manual 28

## Pagina 29

Granularidad del preprocesamiento Transformaciones a nivel de instancia contra pasada completa Alcance de la transformación Congela estadísticas Regla de oro: globales para la Gestión de la inferencia asimetría Transformación Necesita ver todos los datos para el contexto de pase completo Transformación Procesa datos de forma aislada a nivel de instancia 29

## Pagina 30

Transformación del conjunto de datos de entrenamiento Preparación estática antes del entrenamiento Dependencia de la base de datos El modelo depende de estadísticas viejas si la conexión falla, causando errores o datos obsoletos Riesgo Consulta del modelo Tiempo real El modelo consulta la base para obtener el contexto y normalizar datos Guardar constantes Almacenamiento Guardar constantes fijas en una base de datos externa Pasada completa Offline Calcular métricas sobre el historial de datos 30

## Pagina 31

Transformaciones integradas Encapsulación de la lógica y automatización de constantes Mayor latencia El modelo ejecuta cálculos matemáticas extra en tiempo real, aumentando la latencia Desventaja Consistencia total El "paquete hermético" elimina el training-serving Ventaja skew, garantizando resultados idénticos en cualquier lugar Aprendizaje y almacenamiento Acción El modelo aprende y guarda internamente las constantes Preparación integrada Cambio La preparación del dato es parte de la arquitectura del modelo no un paso previo 31

## Pagina 32

¿Dónde realizar el preprocesamiento? Balance entre eficiencia, consistencia y latencia Alta cardinalidad de Baja cardinalidad de datos datos Frecuencia de cambio Frecuencia de cambio baja alta Base de datos Integrado en el externa modelo Datos estáticos Datos transaccionales 32

## Pagina 33

Unidad 3: Gestión de datos Contenido

## 1. Integridad y diseño del dato

## 2. Preprocesamiento de datos

## 3. Metadatos, esquemas y almacenamiento

## Pagina 34

Fases del ciclo de vida del dato en entornos de producción Descripción del flujo desde la ingesta hasta la creación del modelo 34

## Pagina 35

Definición de artefactos en el pipeline Identificación de los resultados generados en cada etapa del proceso 35

## Pagina 36

Implicaciones legales del linaje de datos Requisitos de trazabilidad para el cumplimiento normativo 36

## Pagina 37

Fundamentos de la gestión de metadatos Sistema de registro para el análisis del ciclo de vida del pipeline 37

## Pagina 38

Estructura de las entidades de metadatos Organización de la información para la trazabilidad del sistema 38

## Pagina 39

Definición y función del esquema en producción Estructura técnica para la validación de características 39

## Pagina 40

Adaptación iterativa del esquema Ajuste dinámico del esquema 40

## Pagina 41

Parámetros operativos del sistema Exigencias técnicas en entornos de producción 41

## Pagina 42

Validación según el contexto operativo Adaptación del esquema al entorno 42

## Pagina 43

Repositorios de datos y el reto de producción Del almacenamiento analítico al operacional 43

## Pagina 44

Anatomía de una feature store Gestión centralizada de características 44

## Pagina 45

El repositorio histórico Gestión de datos para entrenamiento masivo 45

## Pagina 46

El repositorio en tiempo real Servicio de baja latencia 46
