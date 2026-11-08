# 05 — Factibilidad y complejidad

## 1. Factibilidad trivial

Antes de resolver, se verifica:

$$
\sum_{t\in T}|A_t|\ge \sum_{g\in G} H_g
$$

y:

$$
\forall m\in \{m_g:g\in G\},\ \exists t\in T: m\in M_t
$$

Si falla, la corrida se marca `ERROR` sin invocar CP-SAT.

## 2. Complejidad

El problema general de asignación de tutores a grupos con restricciones temporales es NP-duro. Se reduce al problema de calendarización con recursos y restricciones de precedencia, que es NP-duro en el caso general.

Por tanto, no existe un algoritmo polinomial conocido que garantice optimalidad para todas las instancias, salvo que $\mathrm{P}=\mathrm{NP}$.

## 3. Uso de CP-SAT

Google OR-Tools CP-SAT utiliza:

- propagación de restricciones,
- búsqueda con backtracking,
- paralelismo con $k$ hilos,
- límite de tiempo $\tau=300$ s.

Si no se prueba optimalidad dentro del límite, se retorna la mejor solución factible encontrada con estado `FEASIBLE` y se reporta el gap.

## 4. Escalabilidad

La complejidad práctica depende de:

- número de grupos $n_G$,
- número de tutores $n_T$,
- número de slots $|S|$,
- densidad de disponibilidad $\rho=\frac{\sum_t |A_t|}{n_T |D||S|}$.

El caché por hash reduce la carga cuando la configuración de entrada es idéntica.

## 5. Implementación

La validación previa se ejecuta en `worker.py` antes de construir el modelo. El timeout se configura con `SOLVER_TIMEOUT`.
