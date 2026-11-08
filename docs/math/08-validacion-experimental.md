# 08 — Validación experimental

## 1. Benchmark del worker

El worker reporta:

$$
\text{tiempo\_solver\_s}=\text{WallTime}(\text{CP-SAT})
$$

y el estado final:

$$
\text{status}\in\{\text{OPTIMAL},\text{FEASIBLE},\text{INFEASIBLE}\}
$$

## 2. Paralelismo

El solver utiliza $k$ hilos:

$$
k=\min(\text{cpu\_count}, \text{configurado})
$$

En `worker.py`:

$$
\text{num\_search\_workers}=k
$$

## 3. Paralelismo de escenarios

Para análisis auxiliares se puede usar `ProcessPoolExecutor` con $p$ procesos, dividiendo $N$ experimentos en lotes de tamaño $L$:

$$
L=\max(10000, \lfloor N/p\rfloor)
$$

## 4. Agregación incremental

Para evitar almacenar $N$ resultados, se mantienen contadores agregados:

$$
\text{Counter}_{\text{global}},\ \text{Counter}_{\text{por dado}},\ \text{Counter}_{\text{eventos}}
$$

La memoria se acota con una muestra de tamaño $M$:

$$
M=3000
$$

## 5. Implementación

El patrón de paralelismo y agregación incremental se adapta de `probability-and-statistics/dice/main.py`. En CUEP se usa para benchmarks y validación, no para el solver CP-SAT.
