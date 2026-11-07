# 06 — Casos de Uso

## Actores

- **Admin**: gestiona usuarios, materias, sedes.
- **Coordinador**: registra tutores, solicita corridas, consulta resultados.
- **Tutor**: consulta su asignación (solo lectura).
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
