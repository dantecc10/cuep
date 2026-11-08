# 03 — Objetivo y restricciones blandas

## 1. Preferencia

Sea $P_1$ el número de asignaciones cuya materia fue marcada como primera preferencia:

$$
P_1=\sum_{g,t,d,s} \mathbf{1}_{\{p_{t,m_g}=1\}}\,x_{g,t,d,s}
$$

## 2. Horas huecas

Para cada tutor y día, las horas huecas son la diferencia entre el intervalo ocupado y las horas de clase:

$$
h_{t,d}= \left(\max_{g,s} s\,x_{g,t,d,s}+b_g\right) - \left(\min_{g,s} s\,x_{g,t,d,s}\right) - \sum_{g,s} b_g\,x_{g,t,d,s}
$$

El total de huecos es:

$$
H=\sum_{t\in T}\sum_{d\in D} h_{t,d}
$$

## 3. Continuidad

La continuidad premia bloques consecutivos del mismo tutor para el mismo grupo. Se modela con una variable auxiliar $c_{g,t,d,s}$ que vale 1 si el bloque $(g,t,d,s)$ es consecutivo al bloque anterior del mismo grupo.

$$
C=\sum_{g,t,d,s} c_{g,t,d,s}
$$

## 4. Balance de carga

La desviación estándar de las cargas asignadas mide el desbalance:

$$
B=\sqrt{\frac{1}{|T|}\sum_{t\in T}\left(c_t-\bar c\right)^2}
$$

donde:

$$
c_t=\sum_{g,d,s} b_g\,x_{g,t,d,s},\qquad \bar c=\frac{1}{|T|}\sum_{t\in T} c_t
$$

## 5. Función objetivo

Se maximiza:

$$
\max Z = W_1 P_1 + W_3 C - W_2 H - W_4 B
$$

con pesos por defecto:

$$
W_1=10,\quad W_2=3,\quad W_3=5,\quad W_4=2
$$

Estos pesos son configurables por corrida mediante `parametros` en `POST /corridas`.

## 6. Implementación

Los términos se agregan en `worker/worker.py` dentro de `solve_corrida`. Las métricas reportadas se persisten en `corridas_horarios.metricas_optimizacion` y se exponen en `GET /corridas/{id}`.
