# 05 — Solver CP-SAT (OR-Tools)

## Objetivo

Asignar tutores a grupos/bloques horarios maximizando preferencias y compactación, respetando restricciones duras.

## Variables

- `x[g,t,d,s]` Bool: grupo `g` asignado a tutor `t` en día `d` slot `s`.
- `y[t,m]` Bool: tutor `t` imparte materia `m` (derivado).
- `h[t,d]` Int: horas huecas del tutor en día `d`.

## Restricciones duras

1. Cada grupo recibe exactamente sus bloques requeridos: `sum(x[g,t,d,s]) = horas_totales/bloque`.
2. Un tutor no se traslapa: para cada `t,d,s`, `sum_g x[g,t,d,s] <= 1`.
3. Disponibilidad: `x[g,t,d,s]=1 ⇒ slot ∈ disponibilidad[t]`.
4. Materia autorizada: `x[g,t,d,s]=1 ⇒ tutor_materias[t, materia[g]]=1`.
5. Capacidad de sala: número de grupos simultáneos por slot ≤ capacidad.
6. Carga máxima: `sum_{g,d,s} x * bloque ≤ carga_max[t]`.

## Restricciones blandas (penalizaciones/bonos en objetivo)

- +W1 por asignación de materia marcada preferencia 1.
- -W2 por cada hora hueca (compactación).
- +W3 por continuidad (mismo tutor en bloques consecutivos del mismo grupo).
- Balance: penalizar desviación de carga respecto a la media (W4).

## Función objetivo

Maximizar: `W1*pref1 + W3*continuidad - W2*huecos - W4*desbalance`.

Pesos por defecto: W1=10, W2=3, W3=5, W4=2 (configurables por corrida).

## Métricas reportadas

- `preferencia_1`: # asignaciones con pref 1.
- `horas_huecas`: total huecos.
- `balance_std`: desviación estándar de cargas.
- `continuidad_score`: bloques consecutivos.
- `tiempo_solver_s`, `status` (OPTIMAL/FEASIBLE/INFEASIBLE).
- `gap` si no óptimo.

## Límites

- Timeout solver: 300s (configurable).
- Threads: número de CPUs locales.
- Si INFEASIBLE, retornar detalle de restricción violada (si es posible).

## Validación previa

Antes de resolver, verificar factibilidad trivial: suma de disponibilidades ≥ horas requeridas; al menos un tutor por materia. Si falla, retornar ERROR sin invocar solver.
