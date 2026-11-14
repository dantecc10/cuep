# 7. Preguntas frecuentes

## ¿CUEP ya está terminado?

No. El repositorio contiene una base de software, documentación de diseño y
partes funcionales del backend, frontend y motor de cálculo. La implementación
de la experiencia completa y su validación con las sedes siguen en desarrollo.

A esto se suma el módulo de inscripción anual, con registro, padrón, mesa de
inscripción, pagos y cierre de ciclo ya construido y en pruebas, pero todavía
en validación con las sedes. Como todo el proyecto, su uso real depende de los
acuerdos de la organización.

## ¿Quién toma la decisión final sobre un horario?

La organización, a través de sus mecanismos de coordinación y sus acuerdos
colectivos. CUEP genera propuestas y facilita revisarlas; no toma decisiones
políticas ni sustituye a las personas.

## ¿Qué pasa si no existe un horario posible?

El sistema debe señalar que no encontró una combinación viable. Eso no es un
fracaso de una persona: puede indicar que faltan tutores, horas, grupos,
espacios o información. La coordinación debe analizar la causa y buscar
alternativas.

## ¿Se puede cambiar un horario después de generarlo?

Sí. Las disponibilidades, grupos y necesidades pueden cambiar. La propuesta debe
revisarse, actualizarse y comunicarse; conservar el historial ayuda a entender
qué cambió.

## ¿El sistema obliga a un tutor a aceptar una asignación?

No debería. La asignación es una propuesta que debe confirmarse mediante los
acuerdos de la organización y respetar las condiciones de cada persona.

## ¿Qué información se guardará?

El diseño contempla información de usuarios, materias, disponibilidad, grupos,
sedes y propuestas de horarios. Además, el proceso de inscripción guarda los
datos del aspirante (nombre, correo, teléfono, dirección, contacto de
emergencia, datos escolares), su matrícula, su pase, las confirmaciones de
asistencia, los cargos y pagos del simulacro, y la bitácora de cada movimiento.

La información personal debe limitarse a lo necesario, protegerse y estar
disponible solo para los roles que la requieren: quien se inscribe en una sede
no ve los datos de otra.

## ¿Por qué el cálculo puede ejecutarse en una computadora local?

Porque buscar entre muchas combinaciones puede exigir más tiempo de cómputo que
el que conviene usar en un servidor pequeño. El diseño separa la gestión de la
información del cálculo: el servidor conserva la coordinación y un equipo local
puede resolver la propuesta. Esto también permite aprovechar equipos existentes.

## ¿CUEP reemplaza las hojas de cálculo?

Busca reducir la dependencia de archivos aislados, pero durante la transición
pueden coexistir ambos recursos. Lo importante es acordar cuál es la fuente
actualizada y evitar que circulen versiones contradictorias.

## ¿Dónde se puede consultar la documentación técnica?

En la carpeta [`docs/`](../). Ahí se explican la arquitectura, los datos, la
API, el motor de optimización, el despliegue, la seguridad y el cierre anual.

## Preguntas del ciclo de inscripción

### ¿Es obligatorio pagar el simulacro?

No. El simulacro es una actividad opcional y el pago nunca es condición para
inscribirse ni para recibir las asesorías.

### ¿Qué es la matrícula?

Es un código corto (por ejemplo `CL0105APG`) que se genera al terminar el
registro. Identifica a la persona dentro del proceso, aparece en el pase y
permite encontrarla en la mesa de inscripción sin exponer más datos de los
necesarios.

### ¿Me pude equivocar con el correo o el teléfono?

El sistema no admite dos registros con el mismo correo ni el mismo teléfono
normalizado, para que una matrícula no se duplique. Si alguien ya se registró
con tus datos, la sede puede ayudarte a localizar el registro.

### ¿Se puede pagar por transferencia?

Sí, si la configuración del ciclo lo habilita. Subes el comprobante en "Mis
pagos" y el personal lo revisa; te llega un aviso cuando se valida o cuando se
rechaza con un motivo. Si el sitio no permite subir archivos, es que el
espacio privado no está configurado: lleva tu comprobante a la sede.

### ¿Qué pasa con mis datos cuando termina el año?

No se borran. El padrón de cada año queda archivado y se puede consultar por
años anteriores. Cuidar cuánto tiempo se conserva esa información también es
parte del proceso.

### ¿Quién puede ver los datos de una persona inscrita?

La persona misma y el personal de su sede. La administración puede ver todas
las sedes, y el personal de otra sede no tiene acceso. Los comprobantes de
pago están en un espacio privado.

### ¿Qué pasa si el registro está cerrado?

Mientras la convocatoria esté cerrada, el sitio no acepta nuevos registros,
pero quienes ya están inscritos pueden entrar a su cuenta a ver su matrícula,
su pase y sus pagos. Cuando la coordinación abre el ciclo, el registro vuelve
a estar disponible.
