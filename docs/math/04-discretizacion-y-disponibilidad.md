# 04 — Discretización temporal y disponibilidad

## 1. Slots

El tiempo se discretiza en horas enteras:

$$
S=\{7,8,\dots,20\}
$$

Un bloque de $b$ horas que inicia en $s$ ocupa los slots:

$$
\{s,s+1,\dots,s+b-1\}
$$

## 2. Conversión de disponibilidad

La disponibilidad declarada como intervalo $[i,f)$ se convierte a conjunto de slots:

$$
A_t=\{(d,h): d\in D,\ i\le h<f,\ h\in S\}
$$

En código, `_time_to_hour` redondea hacia arriba los minutos $\ge 30$:

$$
\phi(\text{HH:MM}) = H + \mathbf{1}_{\{M\ge 30\}}
$$

## 3. Generación de variables

Una variable $x_{g,t,d,s}$ solo se crea si:

$$
\forall h\in\{s,\dots,s+b_g-1\},\quad (d,h)\in A_t
$$

y además:

$$
m_g\in M_t
$$

Esto reduce el espacio de búsqueda y evita restricciones redundantes.

## 4. Capacidad por slot

La capacidad se evalúa a nivel de slot atómico, no de bloque completo. Esto permite traslapes parciales solo cuando la capacidad lo permite.

## 5. Implementación

La disponibilidad se almacena en `disponibilidad_tutor` y se carga en el worker desde `parametros_resumen`. La discretización se aplica en `solve_corrida`.
