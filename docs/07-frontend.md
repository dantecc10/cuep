# 07 — Frontend

## Stack

Next.js 14 (App Router) + TypeScript. UI: Tailwind CSS + shadcn/ui. Estado: TanStack Query + Zustand (auth). Forms: React Hook Form + Zod.

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
| /mi-perfil | Perfil completo del alumno | alumno |
| /mi-credencial | Credencial con matrícula y QR | alumno |
| /registro | Auto-registro de alumno | público |
| /registro-tutor | Auto-registro de tutor voluntario | público |
| /sedes | Sedes públicas con mapa e imagen | público |
| /dashboard | Panel por rol | autenticado |
| /dashboard/sedes | CRUD de sedes | admin |
| /dashboard/planes | Planes de estudio | admin |
| /dashboard/materias | Catálogo de materias | admin |
| /dashboard/usuarios | Gestión de usuarios y roles | admin |
| /dashboard/grupos | Grupos por sede | coord/subcoord |
| /dashboard/tutores | Listado de tutores | coord/subcoord |
| /dashboard/disponibilidad | Disponibilidad y materias del tutor | tutor |
| /dashboard/corridas | Listado y creación de corridas | coord |
| /dashboard/inscripciones | Cupos y pagos | coord/admin |
| /dashboard/publicar | Aprobación y publicación | coord/subcoord |
| /dashboard/mi-horario | Horario publicado del tutor | tutor |
| /dashboard/2fa | Configuración 2FA | autenticado |
| /mi-inscripcion | Inscripción y horario del alumno | alumno |

## Identidad visual

- Tipografía: Anton para titulares, Roboto Slab para textos editoriales, Inter para UI y JetBrains Mono para matrículas, folios y datos técnicos.
- Tratamientos reutilizables: `type-kicker`, `type-deck`, `type-label`, `type-stamp`, `type-quote`, `marker`, `display-outline`.
- Tarjetas: `poster-card`, `poster-card--ink`, `poster-card--paper`, con sombras desplazadas y bordes de tinta.
- Ilustraciones: `heart.png` como emblema y `penguin.png` como presencia recurrente en navegación, vacíos y llamados a la acción.
- Dashboard: sidebar fija en escritorio, navegación horizontal en móvil y `AppShell` compartido por todas las vistas autenticadas.
- Movimiento: una entrada orquestada (`animate-rise`, `animate-stamp`) y respeto a `prefers-reduced-motion`.

## Componentes clave

- `PerfilForm`: nombre, apellidos, teléfono, área, carga máxima, toggle `es_tutor`.
- `RichMarkdownEditor`: editor WYSIWYG (TipTap) que serializa a Markdown; preview.
- `FotoUploader`: crop + upload a R2 con barra de progreso.
- `DisponibilidadGrid`: grilla día×hora (solo si `es_tutor`).
- `MateriaMultiSelect`: con nivel de preferencia.
- `CorridaStatusBadge`: PENDIENTE/PROCESANDO/COMPLETADO/ERROR.
- `HorarioCalendario`: vista semanal por tutor/grupo.
- `SiteChrome`, `SiteHeader`, `SiteFooter`, `HeroSection`, `PaperSection`, `CallToAction`, `AppShell`.
- Assets de identidad: `heart.png` (logo/favicon/emblema) y `penguin.png` (ilustración secundaria).
- `MetricasPanel`: métricas del solver.

## API client

- Axios con interceptor JWT; refresh automático.
- TanStack Query para cache y polling de estado de corrida (cada 3s mientras PENDIENTE/PROCESANDO).

## Validación

- Zod schemas compartidos con backend (generados o duplicados manualmente).
- Mensajes de error desde API mostrados en toast.
