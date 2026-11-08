# Fundamentos matemáticos de CUEP

Este directorio contiene la justificación teórica y las fórmulas que respaldan el sistema de generación de horarios de asesorías BUAP.

## Índice

1. [Notación y modelo de asignación](01-modelo-asignacion.md)
2. [Restricciones duras](02-restricciones-duras.md)
3. [Objetivo y restricciones blandas](03-objetivo-y-restricciones-blandas.md)
4. [Discretización temporal y disponibilidad](04-discretizacion-y-disponibilidad.md)
5. [Factibilidad y complejidad](05-factibilidad-y-complejidad.md)
6. [Métricas de optimización](06-metricas.md)
7. [Hashing y caché](07-hashing-y-cache.md)
8. [Validación experimental](08-validacion-experimental.md)
9. [Apéndice de demostraciones](09-apendice-demostraciones.md)

## Convenciones

- Los conjuntos se denotan con letras mayúsculas: $G$ grupos, $T$ tutores, $D$ días, $S$ slots.
- Las variables binarias se denotan $x_{g,t,d,s}\in\{0,1\}$.
- Los pesos por defecto son $W_1=10$, $W_2=3$, $W_3=5$, $W_4=2$.
- El tiempo se discretiza en bloques de $b$ horas.
- El solver se ejecuta con timeout $\tau=300$ s y $k$ hilos locales.
