# 07 — Frontend

## Stack

React 18 + Vite + TypeScript. UI: Tailwind CSS + shadcn/ui. Estado: TanStack Query + Zustand (auth). Routing: React Router v6. Forms: React Hook Form + Zod.

## Rutas

| Ruta | Página | Rol |
|------|--------|-----|
| /login | Login | público |
| /tutores | Listado tutores | coord/admin |
| /tutores/:id | Detalle/edición | coord/admin |
| /materias | Catálogo | admin |
| /sedes | Sedes | coord/admin |
| /sedes/:id/grupos | Grupos | coord/admin |
| /corridas | Listado corridas | coord |
| /corridas/nueva | Solicitar | coord |
| /corridas/:id | Resultado | coord/tutor |
| /mi-horario | Asignación tutor | tutor |

## Componentes clave

- `PerfilForm`: nombre, apellidos, teléfono, área, carga máxima, toggle `es_tutor`.
- `RichMarkdownEditor`: editor WYSIWYG (TipTap) que serializa a Markdown; preview.
- `FotoUploader`: crop + upload a R2 con barra de progreso.
- `DisponibilidadGrid`: grilla día×hora (solo si `es_tutor`).
- `MateriaMultiSelect`: con nivel de preferencia.
- `CorridaStatusBadge`: PENDIENTE/PROCESANDO/COMPLETADO/ERROR.
- `HorarioCalendario`: vista semanal por tutor/grupo.
- `MetricasPanel`: métricas del solver.

## API client

- Axios con interceptor JWT; refresh automático.
- TanStack Query para cache y polling de estado de corrida (cada 3s mientras PENDIENTE/PROCESANDO).

## Validación

- Zod schemas compartidos con backend (generados o duplicados manualmente).
- Mensajes de error desde API mostrados en toast.
