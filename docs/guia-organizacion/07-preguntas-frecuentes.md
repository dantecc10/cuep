# 7. Preguntas frecuentes

## ¿CUEP ya está terminado?

No. El repositorio contiene una base de software, documentación de diseño y
partes funcionales del backend, frontend y motor de cálculo. La implementación
de la experiencia completa y su validación con las sedes siguen en desarrollo.

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
sedes y propuestas de horarios. La información personal debe limitarse a lo
necesario, protegerse y estar disponible solo para los roles que la requieren.

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
API, el motor de optimización, el despliegue y la seguridad.
