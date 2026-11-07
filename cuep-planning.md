# Especificación de Requerimientos del Sistema: Generación de Horarios BUAP

## 1. Resumen Ejecutivo
El objetivo de este sistema es automatizar y optimizar la asignación de horarios de asesorías para estudiantes de preparatoria y secundaria que aspiran a ingresar a las preparatorias y licencias de la **Benemérita Universidad Autónoma de Puebla (BUAP)**. 

El sistema utiliza una arquitectura híbrida desacoplada (*Heavy Compute Delegation*) donde la administración de datos y la interfaz web residen en un servidor VPS propio, mientras que el motor de cómputo intensivo de optimización se ejecuta en hardware local (la computadora del administrador), garantizando el uso de tecnologías 100% Open Source sin costo de infraestructura por procesamiento.

---

## 2. Requerimientos Funcionales (RF)

### RF-01: Gestión de Voluntarios / Tutores
* **RF-01.1 Captura de Disponibilidad:** Registro de franjas horarias disponibles por día de la semana para cada tutor.
* **RF-01.2 Selección de Áreas y Materias:** Definición de materias que cada tutor está capacitado para impartir según su área de formación principal (ej. Ciencias Exactas, Salud, Sociales, Ingenierías) o áreas adicionales de su conocimiento.
* **RF-01.3 Preferencias y Cargas:** Captura del nivel de preferencia por materia (1ª opción, 2ª opción) y la carga máxima de horas semanales declarada.

### RF-02: Oferta Académica y Perfiles de Ingreso BUAP
* **RF-02.1 Nivel Medio Superior (Prepa BUAP):** Definición de mapas curriculares del examen de admisión a preparatoria (Pensamiento Matemático, Lectura, Redacción, etc.).
* **RF-02.2 Nivel Superior (Licenciatura BUAP):** Configuración de módulos disciplinares específicos según el área o carrera destino (EGEL-I / PAD).
* **RF-02.3 Parámetros de Curso:** Definición de duración en horas por bloque, frecuencia por materia y número de grupos abiertos por sede/módulo.

### RF-03: Generación de Horarios y Motor de Optimización
* **RF-03.1 Restricciones Duras (Mandatorias):**
  * Sin traslape de tutor en un mismo bloque de tiempo.
  * Sin traslape de grupo en una misma materia o bloque.
  * Respeto estricto a las franjas de disponibilidad declaradas por el voluntario.
  * Coincidencia técnica de materias autorizadas/seleccionadas por el tutor.
  * Límite de capacidad de aulas/salas virtuales.
* **RF-03.2 Restricciones Blandas (Deseables/Optimizables):**
  * Maximizar el dictado de materias marcadas como 1ª preferencia del tutor.
  * Minimizar "horas huecas" en la jornada diaria del tutor (compactación).
  * Fomentar la continuidad del docente a lo largo del curso en un mismo grupo.
  * Balancear equitativamente la carga de horas entre voluntarios.

### RF-04: Ejecución Off-Cloud / Worker Local
* **RF-04.1 Desacoplamiento de Cómputo:** El cálculo de combinación óptima debe ejecutarse en la computadora local del coordinador usando Google OR-Tools para no saturar el VPS ni sufrir por tiempos de espera (*timeouts*).
* **RF-04.2 Sistema de Cola de Tareas:** Comunicación vía API REST entre el VPS y el script local para notificar solicitudes `PENDIENTE` y publicar soluciones en estado `COMPLETADO`.

### RF-05: Historial, Versionado y Reuso de Combinaciones (Caché por Hash)
* **RF-05.1 Identificación por Hash SHA-256:** Generación de un hash único basado en la configuración inmutable de entrada (disponibilidades, grupos, áreas) para cada solicitud.
* **RF-05.2 Reuso Inteligente de Resultados:** Si se solicita una nueva combinación y el hash coincide con uno resuelto previamente, el VPS retorna la propuesta al instante sin consumir procesamiento local ni cloud.
* **RF-05.3 Registro de Versiones:** Permitir a los coordinadores guardar, consultar y comparar múltiples propuestas/corridas existentes para una misma sede.

---

## 3. Requerimientos No Funcionales (RNF)

* **RNF-01 Software Libre y Open Source (FOSS):** Todo el stack debe ser 100% gratuito y de código abierto sin dependencia de servicios de suscripción de pago.
* **RNF-02 Seguridad de las Comunicaciones:** Las peticiones entre el Worker local y la API en el VPS se autentican mediante tokens seguros (JWT / API Keys) con tráfico encriptado HTTPS/SSL.
* **RNF-03 Portabilidad del Entorno:** La infraestructura del servidor debe estar empaquetada mediante **Docker Compose** para garantizar despliegues limpios en cualquier servidor VPS Linux.
* **RNF-04 Escalabilidad y Persistencia:** La base de datos estará estructurada sobre PostgreSQL para soportar relaciones complejas de muchos a muchos de manera eficiente.

---

## 4. Arquitectura de Software Planteada

```
+-------------------------------------------------------------------------+
|                              VPS (SERVIDOR)                             |
|                                                                         |
|  +------------------+         +----------------+     +---------------+  |
|  |   Frontend Web   | <-----> |   FastAPI      | <-> |  PostgreSQL   |  |
|  |  (React/Vue.js)  |         |   Backend      |     |  Base Datos   |  |
|  +------------------+         +-------+--------+     +---------------+  |
+---------------------------------------|---------------------------------+
                                        | API REST (HTTPS + SSL)
                                        v
+-------------------------------------------------------------------------+
|                           COMPUTADORA LOCAL                             |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  |                        Python Worker                              |  |
|  |    * Polling de tareas pendientes                                  |  |
|  |    * Solver: Google OR-Tools (CP-SAT)                             |  |
|  |    * Devuelve JSON de asignaciones y métricas                     |  |
|  +-------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
```

---

## 5. Esquema Preliminar de Base de Datos (PostgreSQL)

```sql
-- 1. Usuarios y Coordinadores
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    rol VARCHAR(20) NOT NULL -- 'coordinador', 'tutor'
);

-- 2. Materias según oferta BUAP (Prepa y Módulos de Licenciatura)
CREATE TABLE materias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    nivel VARCHAR(20) NOT NULL, -- 'PREPA', 'LICENCIATURA'
    area VARCHAR(50) NOT NULL    -- 'Exactas', 'Salud', 'Sociales', etc.
);

-- 3. Disponibilidad del Tutor
CREATE TABLE disponibilidad_tutor (
    id SERIAL PRIMARY KEY,
    tutor_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
    dia_semana INT NOT NULL, -- 1=Lunes ... 6=Sábado
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL
);

-- 4. Materias Habilitadas por Tutor
CREATE TABLE tutor_materias (
    tutor_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
    materia_id INT REFERENCES materias(id) ON DELETE CASCADE,
    nivel_preferencia INT DEFAULT 1, -- 1=Alta, 2=Media, 3=Baja
    PRIMARY KEY (tutor_id, materia_id)
);

-- 5. Historial de Corridas / Generaciones de Horarios
CREATE TABLE corridas_horarios (
    id SERIAL PRIMARY KEY,
    config_hash VARCHAR(64) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE', -- 'PENDIENTE', 'PROCESANDO', 'COMPLETADO', 'ERROR'
    solicitado_por VARCHAR(100),
    parametros_resumen JSONB,
    resultado_json JSONB,
    metricas_optimizacion JSONB,
    creado_en TIMESTAMP DEFAULT NOW(),
    actualizado_en TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_corridas_hash ON corridas_horarios(config_hash);
```