# 10 — Cierre y apertura anual

## Qué resuelve

El ciclo de inscripción del CUEP es anual: cada cohorte recibe matrículas,
pases, cargos y comprobantes propios. Al terminar el ciclo hay que **cerrar el
registro**, **cambiar el año activo** y **abrir el registro del año siguiente**
sin perder la información histórica del ciclo saliente.

Este runbook cubre ese paso con `backend/scripts/reset_academic_year.py`, un
script de mantenimiento que:

- cierra el registro y adelanta el año activo en `configuracion_inscripcion`;
- exporta el padrón del ciclo saliente a CSV;
- opcionalmente crea un respaldo `pg_dump` antes de tocar la base;
- opcionalmente borra los aspirantes demo generados por el seed;
- **nunca** borra ni modifica a las personas, cargos, pagos o eventos del ciclo
  anterior.

## Cuándo ejecutarlo

- Al cerrar la convocatoria del ciclo vigente, antes de abrir la siguiente.
- No hace falta ejecutarlo si sólo quieres pausar la registrations: usa
  `/dashboard/configuracion-inscripcion` y desactiva *Registro abierto*.

## Pre-requisitos

1. Base de datos respaldada y verificada (restaurable).
2. Sin pagos en estado `pendiente` sin revisar: los comprobantes pendientes se
   validan antes del cierre.
3. Sin notificaciones en `error` en el outbox.
4. `pg_dump` disponible en el servidor (`postgresql-client`).
5. Conocimiento del año destino: por ejemplo `2026 → 2027`.

## Procedimiento

### 1. Simula el cierre

Usa el script en modo `--dry-run` primero: no escribe nada, pero muestra el
año de origen, el año destino y el padrón saliente.

```bash
cd /opt/cuep/backend
source .venv/bin/activate
python scripts/reset_academic_year.py --year 2027 --dry-run
```

### 2. Ejecuta el cierre

```bash
python scripts/reset_academic_year.py \
  --year 2027 \
  --confirm "RESET 2027" \
  --backup /opt/cuep/backups/cuep-pre-cierre-2026.sql \
  --export-csv /opt/cuep/backups/inscripciones-2026.csv
```

La frase de confirmación debe ser exacta (`RESET <anio>`); el script se niega a
escribir sin ella. Al terminar:

- `configuracion_inscripcion.anio` = nuevo año;
- `configuracion_inscripcion.registro_abierto` = `false` (queda cerrado para
  que la administración revise simulacro, banco y parcialidades);
- el padrón del año saliente sigue en la base y se consulta por `anio`.

### 3. Revisa la configuración del nuevo ciclo

Entra a `/dashboard/configuracion-inscripcion` y ajusta:

- año activo (debe coincidir con el nuevo);
- monto y activación del simulacro;
- datos de transferencia (banco, titular, CLABE, instrucciones);
- efectivo, parcialidades y donativo;
- **Registro abierto** cuando la convocatoria esté lista.

Alternativa por API (admin):

```bash
curl -X PUT https://app.example.com/api/v1/inscripciones/config \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"anio":2027,"registro_abierto":true,"simulacro_activo":true,"simulacro_monto":150}'
```

### 4. Verifica

```bash
curl -s https://app.example.com/api/v1/inscripciones/config | jq
curl -s "https://app.example.com/api/v1/inscripciones?anio=2026&page_size=1" -H "Authorization: Bearer $TOKEN" | jq .total
```

Comprueba que:

- el año activo es el nuevo;
- el padrón del año anterior sigue disponible con `?anio=<año_anterior>`;
- un registro nuevo genera matrícula del nuevo ciclo;
- el pase y el QR se descargan sin errores.

### 5. Limpieza de datos demo (opcional)

En staging o entornos de prueba puedes eliminar los aspirantes del seed:

```bash
python scripts/reset_academic_year.py \
  --year 2027 --confirm "RESET 2027" --purge-demo
```

Borra únicamente registros con `registration_source = 'seed'` y correo
`@cuep.example.com` del ciclo saliente, junto con sus cargos, pagos, eventos y
notificaciones. **No lo ejecutes contra datos reales.**

## Parámetros del script

| Parámetro | Descripción |
|---|---|
| `--year N` | Año del nuevo ciclo. Por defecto `año vigente + 1`. |
| `--close-only` | Sólo cierra el registro del año vigente (confirmación `CLOSE <anio>`). |
| `--open-registration` | Deja el nuevo ciclo con el registro abierto. Por defecto queda cerrado. |
| `--export-csv RUTA` | Exporta el padrón del ciclo saliente. |
| `--backup RUTA` | Respaldo `pg_dump` previo (no se permite con `--dry-run`). |
| `--purge-demo` | Borra aspirantes demo del ciclo saliente. |
| `--confirm FRASE` | `RESET <anio>` o `CLOSE <anio>`. Obligatorio para escribir. |
| `--dry-run` | Muestra el plan y no escribe nada. |

## Qué se conserva y qué cambia

| Elemento | Tras el cierre |
|---|---|
| `students` del ciclo anterior | Se conservan (histórico, filtrable por `anio`). |
| Matrículas, folios y `qr_token` | No se tocan; el folio es global y no se reinicia. |
| Cargos, pagos y comprobantes | Se conservan. |
| `eventos_inscripcion` | Se conservan (bitácora). |
| `configuracion_inscripcion.anio` | Cambia al año destino. |
| `configuracion_inscripcion.registro_abierto` | Pasa a `false` (o `true` con `--open-registration`). |
| Nuevos registros | Se etiquetan con el año activo. |

## Reversión

Si algo salió mal, restaura el respaldo:

```bash
sudo systemctl stop cuep-api
sudo -u postgres psql cuep < /opt/cuep/backups/cuep-pre-cierre-2026.sql
sudo systemctl start cuep-api
```

Para un cambio de año sin pérdida de datos basta con corregir la configuración:

```sql
UPDATE configuracion_inscripcion
SET anio = 2026, registro_abierto = true
WHERE id = 1;
```

## Checklist de fin de ciclo

- [ ] Respaldo verificado y guardado fuera del servidor.
- [ ] Padrón del ciclo saliente exportado a CSV.
- [ ] Pagos pendientes revisados y comprobantes validados o rechazados.
- [ ] Notificaciones del outbox sin errores.
- [ ] Script ejecutado con confirmación y sin advertencias.
- [ ] Año activo actualizado y registro cerrado.
- [ ] Configuración del nuevo ciclo revisada (simulacro, banco, efectivo).
- [ ] Registro abierto cuando la convocatoria esté activa.
- [ ] Prueba de registro real con matrícula y QR.
- [ ] Demo purge sólo en entornos de prueba, si aplica.
