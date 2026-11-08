# 01 — Notación y modelo de asignación

## 1. Conjuntos

Sea:

- $G=\{1,\dots,n_G\}$ el conjunto de grupos.
- $T=\{1,\dots,n_T\}$ el conjunto de tutores con $es\_tutor=\top$.
- $M=\{1,\dots,n_M\}$ el conjunto de materias.
- $D=\{1,\dots,6\}$ los días de la semana (lunes a sábado).
- $S=\{7,\dots,20\}$ los slots horarios discretos en horas.

Cada grupo $g\in G$ tiene:

- materia $m_g\in M$,
- horas totales $H_g\in\mathbb{Z}_{>0}$,
- tamaño de bloque $b_g\in\mathbb{Z}_{>0}$,
- número de bloques requeridos $n_g=\lfloor H_g/b_g\rfloor$.

Cada tutor $t\in T$ tiene:

- carga máxima $C_t\in\mathbb{Z}_{\ge 0}$,
- materias autorizadas $M_t\subseteq M$ con preferencia $p_{t,m}\in\{1,2,3\}$,
- disponibilidad $A_t\subseteq D\times S$.

## 2. Variables

Variable principal de asignación:

$$
x_{g,t,d,s}\in\{0,1\},\quad \forall g\in G,\ t\in T,\ d\in D,\ s\in S
$$

donde $x_{g,t,d,s}=1$ si el grupo $g$ se asigna al tutor $t$ en el día $d$ a partir del slot $s$ por $b_g$ horas consecutivas.

Variables derivadas:

$$
y_{t,m}=\bigvee_{g:m_g=m}\bigvee_{d,s} x_{g,t,d,s}
$$

$$
h_{t,d}\in\mathbb{Z}_{\ge 0}
$$

donde $h_{t,d}$ representa las horas huecas del tutor $t$ en el día $d$.

## 3. Implementación

La formulación se implementa en `worker/worker.py` mediante `ortools.sat.python.cp_model.CpModel`. La capa de persistencia y la API se definen en `backend/app/routers/corridas.py` y `backend/app/models/corrida.py`.

La discretización y la disponibilidad se detallan en [04-discretizacion-y-disponibilidad.md](04-discretizacion-y-disponibilidad.md).
