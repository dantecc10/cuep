# 07 — Hashing y caché

## 1. Entrada inmutable

La entrada de una corrida se serializa como JSON canónico:

$$
J=\mathrm{JSON}_{\text{canónico}}(\text{tutores},\text{disponibilidad},\text{materias},\text{grupos},\text{parámetros})
$$

con claves ordenadas y sin espacios.

## 2. Hash SHA-256

$$
h=\mathrm{SHA256}(J)
$$

El hash se almacena en `corridas_horarios.config_hash`.

## 3. Caché

Si existe una corrida con el mismo hash y estado `COMPLETADO`, se retorna el resultado sin ejecutar el solver:

$$
\text{cache\_hit}=\exists c: c.config\_hash=h \land c.estado=\text{COMPLETADO}
$$

Si existe en `PENDIENTE` o `PROCESANDO`, se reutiliza la misma tarea para evitar duplicados.

## 4. Probabilidad de colisión

Para SHA-256, la probabilidad de colisión accidental es:

$$
P_{\text{colisión}}\approx 2^{-256}
$$

Esto hace que el caché sea seguro para configuraciones inmutables.

## 5. Implementación

El hash se calcula en `_build_canonical` dentro de `backend/app/routers/corridas.py`. La deduplicación se realiza antes de insertar una nueva corrida.
