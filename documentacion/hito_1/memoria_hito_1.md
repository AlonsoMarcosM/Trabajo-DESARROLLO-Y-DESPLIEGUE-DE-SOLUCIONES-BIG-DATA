\documentclass[12pt,a4paper]{article}

\usepackage[spanish]{babel}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{hyperref}
\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{longtable}
\geometry{margin=2.5cm}

\title{\textbf{Hito 1: Alcance y viabilidad}}
\author{
\textbf{Asignatura:} Desarrollo y Despliegue de Soluciones Big Data \\
\textbf{Máster:} Máster Universitario en Big Data y Computación en la Nube \\
\textbf{Curso académico:} 2025--2026 \\
\\
Alonso Marcos Muñoz \\
\texttt{Alonso.Marcos@alu.uclm.es} \\
\\
Jose Barros Ribademar \\
\texttt{Jose.Barros1@alu.uclm.es}
}
\date{Febrero de 2026}

\begin{document}

\maketitle
\tableofcontents
\newpage

\section*{Datos de la entrega}

\begin{itemize}
    \item Asignatura: \textbf{DESARROLLO Y DESPLIEGUE DE SOLUCIONES BIG DATA}
    \item Máster: \textbf{Máster Universitario en Big Data y Computación en la Nube}
    \item Curso académico: 2025--2026
    \item Integrantes:
    \begin{itemize}
        \item Alonso Marcos Muñoz (\texttt{Alonso.Marcos@alu.uclm.es})
        \item Jose Barros Ribademar (\texttt{Jose.Barros1@alu.uclm.es})
    \end{itemize}
    \item Fecha de elaboración: febrero de 2026
\end{itemize}

\section{Introducción del hito}

Este primer hito cierra el alcance del proyecto antes de entrar en la fase técnica de implementación. El objetivo no es solo describir el problema de negocio, sino justificar por qué tiene sentido abordarlo con una solución de datos, qué valor económico realista puede aportar y cómo se va a ejecutar con recursos limitados, en el calendario oficial de la asignatura.

La propuesta se ha redactado con un enfoque deliberadamente alcanzable: empezar con una primera versión funcional (MVP) y evitar compromisos técnicos innecesarios para una entrega inicial. Esta decisión mantiene el equilibrio entre rigor académico, viabilidad de ejecución en pareja y potencial de mejora en los hitos siguientes.

Fecha oficial de cierre del hito: \textbf{27 de febrero de 2026}.

\section{Alcance y viabilidad}

\subsection{Definición del problema de negocio}

La operadora de telecomunicaciones gestiona una base de datos activa de 2.000.000 de clientes particulares en un mercado altamente saturado. Actualmente, la compañía se enfrenta a una tasa de rotación mensual del 3\% (60.000 clientes abandonan la compañía cada mes), una hemorragia que las campañas de fidelización genéricas no logran detener.

Esta falta de inteligencia comercial genera un impacto negativo por dos vías:

\begin{itemize}
    \item \textbf{Fugas recuperables no evitadas}: 40.000 usuarios recuperables abandonan la compañía cada mes.  
    Con un valor de vida promedio perdido por cliente de 100 euros de margen neto anual:

    \[
    40.000 \times 100 = 4.000.000 \text{ EUR/mes}
    \]

    \item \textbf{Incentivos mal asignados}: descuentos ofrecidos al 5\% de la base leal (100.000 clientes).  
    Con coste medio de 10 euros por descuento:

    \[
    100.000 \times 10 = 1.000.000 \text{ EUR/mes}
    \]
\end{itemize}

Pérdida total operativa:

\[
4.000.000 + 1.000.000 = 5.000.000 \text{ EUR/mes}
\]

\subsection{Planteamiento y selección de la solución técnica}

Se compararon tres alternativas: heurística por reglas, ML en servidor monolítico y arquitectura big data distribuida.

\begin{longtable}{p{4cm}p{2.5cm}p{2.5cm}p{3cm}}
\toprule
\textbf{Criterio de decisión} & \textbf{Heurística} & \textbf{ML monolítico} & \textbf{Big Data (MVP)} \\
\midrule
Escalabilidad con 2M clientes & Baja & Media & Alta \\
Esfuerzo de mantenimiento & Alto & Medio & Medio \\
Integración de nuevas fuentes & Baja & Media & Alta \\
Trazabilidad & Baja & Media & Alta \\
Riesgo de obsolescencia & Alto & Medio & Bajo \\
\bottomrule
\end{longtable}

Se selecciona \textbf{Big Data distribuido} en versión mínima viable (MVP).

\subsection{Evaluación de la viabilidad y valor}

\subsubsection{Viabilidad técnica}

\begin{enumerate}
    \item Masa crítica suficiente (2 millones de clientes activos).
    \item Problema de clasificación supervisada natural.
    \item Señales predictivas razonables: antigüedad, uso de servicios, incidencias, facturación, interacción con campañas.
    \item Diseño batch que reduce riesgo de implementación inicial.
\end{enumerate}

\subsubsection{Viabilidad económica (escenario conservador)}

Pérdidas mensuales declaradas:

\begin{itemize}
    \item Fugas recuperables: 4.000.000 EUR/mes
    \item Incentivos mal asignados: 1.000.000 EUR/mes
\end{itemize}

Escenario MVP:

\begin{itemize}
    \item Reducción 5\% fuga recuperable: $4.000.000 \times 0,05 = 200.000$ EUR/mes
    \item Reducción 5\% descuentos innecesarios: $1.000.000 \times 0,05 = 50.000$ EUR/mes
\end{itemize}

\[
\text{Beneficio total} = 200.000 + 50.000 = 250.000 \text{ EUR/mes}
\]

Costes:

\begin{itemize}
    \item Equipo técnico: 10.000 EUR/mes
    \item Infraestructura cloud: 1.100 EUR/mes
\end{itemize}

\[
\text{Coste total} = 10.000 + 1.100 = 11.100 \text{ EUR/mes}
\]

\[
\text{ROI} = \left(\frac{250.000 - 11.100}{11.100}\right)\times 100 = 2152\%
\]

\[
\text{Payback} = \frac{11.100}{250.000}\times 30 = 1,3 \text{ días}
\]

\subsubsection{Viabilidad ética y legal}

\begin{enumerate}
    \item Seudonimización y control de accesos.
    \item Trazabilidad de datasets y modelos.
    \item Métrica de fairness: Equal Opportunity Difference.
\end{enumerate}

\subsection{Planificación y recursos}

\subsubsection{KPIs de negocio y traducción técnica}

\begin{itemize}
    \item Reducir en 5\% la pérdida por fuga recuperable.
    \item Reducir en 5\% el coste por incentivos innecesarios.
\end{itemize}

Estudios de referencia: \url{https://medium.com/%40avk8923/case-2-out-of-15-7fa38feff88c}

Traducción a magnitudes operativas:

\begin{itemize}
    \item Fuga recuperable: 40.000 → 38.000 clientes/mes
    \item Incentivos mal asignados: 100.000 → 95.000 clientes/mes
\end{itemize}

Metas técnicas iniciales:

\begin{itemize}
    \item Mejorar detección de clientes con riesgo real de baja
    \item Incrementar precisión de campañas evitando descuentos innecesarios
    \item Priorizar estabilidad y reproducibilidad frente a optimización agresiva
\end{itemize}

\subsubsection{Equipo de trabajo}

\begin{itemize}
    \item Ingeniería de datos/MLOps: ingesta, calidad de datos, orquestación y ejecución
    \item Modelado: construcción de variables, entrenamiento, evaluación y análisis de error
\end{itemize}

\subsubsection{Fuentes y stack tecnológico}

Fuentes mínimas:

\begin{itemize}
    \item Maestro de clientes
    \item Histórico de bajas/churn
    \item Uso de servicios y facturación
    \item Histórico de campañas y respuesta
\end{itemize}

Stack tecnológico:

\begin{itemize}
    \item Databricks + Delta Lake
    \item Spark (batch)
    \item Spark MLlib
    \item MLflow
    \item GitHub
\end{itemize}

\subsubsection{Cronograma oficial del proyecto}

\begin{itemize}
    \item Hito 1: Alcance y viabilidad – 24/02/2026 a 27/02/2026
    \item Hito 2: Preparación y gestión de datos – 28/02/2026 a 20/03/2026
    \item Hito 3: Modelado y experimentación – 21/03/2026 a 17/04/2026
    \item Hito 4: Despliegue y monitorización – 18/04/2026 a 01/05/2026
\end{itemize}

\section{Cierre del hito}

El alcance queda cerrado con una propuesta coherente en las cuatro dimensiones exigidas: definición del problema, selección técnica razonada, viabilidad completa y planificación.

La estrategia adoptada evita promesas difíciles de sostener y prioriza una entrega sólida, medible y defendible. El siguiente paso es ejecutar el hito 2 para validar calidad del dato y materializar la arquitectura en Databricks.

\end{document}