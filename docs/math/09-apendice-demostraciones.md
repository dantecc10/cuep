# 09 — Apéndice de demostraciones

## 1. NP-dureza del timetabling

El problema de asignación de tutores a grupos con restricciones temporales generaliza el problema de calendarización con recursos, que es NP-duro. Por reducción polinomial desde una instancia de satisfacibilidad o calendarización, se concluye que no existe un algoritmo polinomial general para todas las instancias.

## 2. Correctitud de la factibilidad trivial

Si $\sum_t |A_t|<\sum_g H_g$, entonces por el principio del palomar no existe asignación que cubra todas las horas requeridas. Por tanto, la instancia es infeasible.

Si alguna materia requerida no tiene tutor habilitado, entonces ningún grupo de esa materia puede asignarse, lo que también implica infeasibilidad.

## 3. Seguridad del hash

SHA-256 es una función de hash criptográfica con salida de 256 bits. Bajo el modelo de oráculo aleatorio, la probabilidad de colisión para $n$ entradas es aproximadamente:

$$
P_{\text{colisión}}\approx \frac{n^2}{2^{257}}
$$

Para $n\ll 2^{128}$, esta probabilidad es despreciable.

## 4. Cota de huecos

Para un tutor con bloques en un día, la cantidad mínima de huecos es:

$$
h_{t,d}\ge 0
$$

y se alcanza cuando los bloques son contiguos.

## 5. Referencias internas

- `docs/05-solver-cpsat.md`
- `worker/worker.py`
- `backend/app/routers/corridas.py`
- `backend/app/models/corrida.py`
