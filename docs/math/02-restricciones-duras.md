# 02 — Restricciones duras

Las restricciones duras son mandatorias. Si alguna no puede satisfacerse, la corrida debe terminar en estado `INFEASIBLE` o `ERROR`.

## 1. Cobertura de grupos

Cada grupo debe recibir exactamente sus bloques requeridos:

$$
\sum_{t\in T}\sum_{d\in D}\sum_{s\in S} x_{g,t,d,s}=n_g,\quad \forall g\in G
$$

## 2. No traslape de tutor

Un tutor no puede atender dos grupos en el mismo slot atómico:

$$
\sum_{g\in G}\sum_{s'=s-b_g+1}^{s} x_{g,t,d,s'}\le 1,\quad \forall t,d,s
$$

## 3. Disponibilidad

La asignación solo puede ocurrir si todos los slots del bloque pertenecen a la disponibilidad del tutor:

$$
x_{g,t,d,s}=1 \implies \{(d,s),(d,s+1),\dots,(d,s+b_g-1)\}\subseteq A_t
$$

En CP-SAT esta implicación se modela creando la variable únicamente cuando la condición se cumple.

## 4. Materia autorizada

Un tutor solo puede impartir materias para las que está habilitado:

$$
x_{g,t,d,s}=1 \implies m_g\in M_t
$$

## 5. Capacidad de sala

El número de grupos simultáneos en un slot no puede exceder la capacidad:

$$
\sum_{g\in G}\sum_{t\in T}\sum_{s'=s-b_g+1}^{s} x_{g,t,d,s'}\le K_{d,s},\quad \forall d,s
$$

donde $K_{d,s}$ es la capacidad disponible en el slot $(d,s)$.

## 6. Carga máxima

La carga asignada a un tutor no puede exceder su límite declarado:

$$
\sum_{g\in G}\sum_{d\in D}\sum_{s\in S} b_g\,x_{g,t,d,s}\le C_t,\quad \forall t\in T
$$

## Validación previa

Antes de invocar el solver, el worker verifica factibilidad trivial:

$$
\sum_{t\in T}|A_t|\ge \sum_{g\in G} H_g
$$

y que cada materia tenga al menos un tutor habilitado:

$$
\forall m\in \{m_g:g\in G\},\ \exists t\in T: m\in M_t
$$

Si alguna falla, se retorna `ERROR` sin consumir el solver.
