# 06 — Métricas de optimización

Las métricas se calculan a partir de la solución y se persisten en `metricas_optimizacion`.

## 1. Preferencia de primera opción

$$
\text{preferencia\_1}=\sum_{g,t,d,s} \mathbf{1}_{\{p_{t,m_g}=1\}}\,x_{g,t,d,s}
$$

## 2. Horas huecas

$$
\text{horas\_huecas}=\sum_{t\in T}\sum_{d\in D} h_{t,d}
$$

## 3. Balance

Desviación estándar de cargas:

$$
\text{balance\_std}=\sqrt{\frac{1}{|T|}\sum_{t\in T}(c_t-\bar c)^2}
$$

## 4. Continuidad

$$
\text{continuidad\_score}=\sum_{g,t,d,s} c_{g,t,d,s}
$$

## 5. Tiempo de solver

$$
\text{tiempo\_solver\_s}=\text{WallTime}(\text{CP-SAT})
$$

## 6. Gap

Si el solver termina por timeout, se reporta:

$$
\text{gap}=\frac{Z^*-Z_{\text{best}}}{Z^*}
$$

donde $Z^*$ es la cota superior y $Z_{\text{best}}$ la mejor solución encontrada.

## 7. Implementación

Las métricas se construyen en `solve_corrida` y se envían a `POST /worker/tareas/{id}/resultado`. La API las almacena en `CorridaHorario.metricas_optimizacion`.
