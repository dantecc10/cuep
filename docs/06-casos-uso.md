# 06 — Casos de Uso

## Actores

- **Admin**: gestiona usuarios, materias, sedes y la configuración del ciclo de inscripción.
- **Coordinador**: registra tutores, solicita corridas, consulta resultados.
- **Subcoordinador**: apoya al coordinador en su sede.
- **Personal de inscripción** (rol `inscripcion`): opera el padrón de su sede, confirma asistencia y cobra en efectivo.
- **Tutor**: consulta su asignación (solo lectura).
- **Alumno**: se registra, recibe matrícula y pase, paga el simulacro y consulta su inscripción.
- **Worker**: proceso automatizado.

## Casos de uso principales

### UC-01 Registrar tutor
Actor: Coordinador. Flujo: captura datos → disponibilidad → materias/preferencias → carga máxima. Criterio: tutor queda activo y consultable.

### UC-02 Configurar oferta académica
Actor: Admin. Alta de materias por nivel/área y parámetros (horas/bloque, frecuencia).

### UC-03 Crear grupos por sede
Actor: Coordinador. Define grupos (materia, horas totales, capacidad).

### UC-04 Solicitar generación de horarios
Actor: Coordinador. Selecciona sede + grupos + parámetros → sistema crea corrida, retorna hash y estado. Si cache hit, resultado inmediato.

### UC-05 Procesar tarea (Worker)
Actor: Worker. Polling → toma tarea → resuelve → publica resultado.

### UC-06 Consultar resultado
Actor: Coordinador. Ve asignaciones por tutor/grupo, métricas, estado. Puede reintentar si ERROR.

### UC-07 Versionado/comparación
Actor: Coordinador. Lista corridas por sede, compara métricas entre versiones.

## Criterios de aceptación (solicitud de corrida)

- Respuesta < 500ms cuando cache hit.
- Estado inicial `PENDIENTE`.
- Hash reproducible para misma entrada.
- Worker procesa en < 5 min para 20 tutores / 10 grupos.


### UC-08 Registrar alumno
Actor: Alumno. Flujo: auto-registro con sede, nivel y área → perfil creado. Criterio: alumno puede iniciar sesión.

### UC-09 Inscribirse a grupo
Actor: Alumno. Flujo: consulta grupos disponibles → inscripción → confirmada, pendiente de pago o lista de espera. Criterio: cupo respetado y notificación enviada.

### UC-10 Cancelar inscripción
Actor: Alumno. Flujo: cancela inscripción → si había cupo, promoción automática del siguiente en lista de espera. Criterio: cupo liberado y promoción notificada.

### UC-11 Consultar asignación
Actor: Alumno. Flujo: consulta su grupo y tutor asignado tras corrida completada. Criterio: información visible.

## Ciclo de inscripción anual

### UC-12 Registrarse como aspirante
Actor: Alumno (público). Flujo: formulario de 3 pasos (cuenta, datos personales, datos académicos) → se crea usuario con rol `alumno` y perfil de aspirante → se genera folio y matrícula con la sede elegida.
Criterios de aceptación:
- El registro falla con 403 si `registro_abierto` es falso.
- Correo y teléfono normalizados son únicos; el duplicado devuelve 409.
- La matrícula tiene el formato `{sede}{P|L}{folio:04d}{iniciales}` y no se edita después.
- El evento `registro` queda en la bitácora con su origen (`web`).
- Si la persona marca el opt-in del simulacro, se crea un cargo del año vigente.

### UC-13 Consultar inscripción, pase y QR
Actor: Alumno. Flujo: `/mi-registro` muestra estatus, matrícula, QR, pase, cargos y pagos recientes; puede descargar el PDF del pase.
Criterios de aceptación:
- Sólo el titular de la cuenta ve su información.
- El QR apunta a `/mi-registro?token=<qr_token>` y sirve para el check-in presencial.
- Los pagos y eventos mostrados corresponden al alumno.

### UC-14 Confirmar asistencia en sede (check-in)
Actor: Personal de inscripción / coordinador. Flujo: captura la matrícula, escanea el QR o busca por correo/teléfono → se registra `checkin_at`, `checkin_by` y `checkin_sede_id`.
Criterios de aceptación:
- Un aspirante con estatus `cancelado` o `baja` no puede hacer check-in (409).
- El rol `inscripcion` sólo opera su sede; el admin puede operar todas.
- Un segundo check-in no duplica el evento ni la hora registrada.
- Se encola la notificación `checkin_confirmado`.

### UC-15 Participar en el simulacro y pagar
Actor: Alumno. Flujo: activa el opt-in (formulario o `Mis pagos`) → aparece el cargo → paga en efectivo en sede o por transferencia con comprobante.
Criterios de aceptación:
- El simulacro es opcional y no bloquea la inscripción.
- Existe como máximo un cargo `simulacro` por alumno y año.
- Los alumnos sólo pueden registrar pagos por `transferencia`; el efectivo lo captura el personal de sede.
- Sin `R2_PRIVATE_BUCKET` configurado, la subida de comprobante devuelve 503.

### UC-16 Validar o rechazar una transferencia
Actor: Coordinador / subcoordinador / admin. Flujo: `/dashboard/pagos` lista los pagos por validar → se revisa el comprobante (URL firmada) → se aprueba o se rechaza con motivo.
Criterios de aceptación:
- Sólo los roles `admin`, `coordinador` y `subcoordinador` validan; `inscripcion` no.
- Al validar se genera el código de recibo y se notifica `pago_validado`; al rechazar, `pago_rechazado` con motivo.
- El recibo en PDF sólo se descarga con un pago `validado`.

### UC-17 Consultar y exportar el padrón
Actor: Admin / coordinador / subcoordinador. Flujo: `/dashboard/aspirantes` filtra por año, sede, estatus, nivel y área → revisa el detalle del alumno → exporta CSV.
Criterios de aceptación:
- Los roles distintos de admin ven sólo su sede.
- La exportación CSV requiere rol `admin`, `coordinador` o `subcoordinador`.
- El padrón del año anterior sigue consultable con el filtro `anio`.

### UC-18 Enviar notificaciones
Actor: Admin (o worker). Flujo: se encola un aviso con plantilla → el worker (o `POST /notificaciones/procesar`) envía el correo y actualiza el estado del outbox.
Criterios de aceptación:
- La cola deduplica por `dedupe_key`.
- Los envíos fallidos quedan en `error` con `ultimo_error` y pueden reintentarse.
- El rol `inscripcion` no accede a plantillas ni outbox.

### UC-19 Cerrar el ciclo y abrir el siguiente
Actor: Admin (o con el script de mantenimiento). Flujo: se exporta el padrón y se respalda la base → `scripts/reset_academic_year.py --year <n> --confirm "RESET <n>"` adelanta el año activo y cierra el registro → se revisa la configuración del nuevo ciclo → se abre el registro.
Criterios de aceptación:
- El script exige la frase de confirmación exacta y no escribe en modo `--dry-run`.
- Los alumnos, cargos, pagos y eventos del ciclo anterior no se modifican.
- El nuevo ciclo exige revisión de simulacro, banco y efectivo antes de abrir el registro.
- Detalle completo en [10 — Cierre y Apertura Anual](10-cierre-anual.md).

### UC-20 Asignar grupos a los inscritos
Actor: Personal de inscripción (su sede), coordinador o administración. Flujo: se
consulta el detalle del aspirante → se asigna un grupo con
`POST /inscripciones/{id}/grupos` → el alumno recibe el aviso.
Criterios de aceptación:
- El grupo debe ser de la sede del alumno y tener el mismo nivel y área.
- No se puede asignar dos veces el mismo grupo (409).
- Si el grupo está lleno y la sede tiene lista de espera, la asignación queda
  en `lista_espera`; si no, responde 409.
- Cada asignación deja un evento `asignacion_grupo` en la bitácora y encola la
  notificación `grupo_asignado`.
- El rol `inscripcion` sólo opera su sede; otra sede recibe 403.
- Los alumnos no pueden asignarse grupos a sí mismos.
