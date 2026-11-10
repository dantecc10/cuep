# Guía de identidad gráfica y sistema visual

## Integración del sitio web del Colectivo Universitario por la Educación Popular (CUEP-AP)

**Versión:** 1.0\
**Propósito:** servir como documento de contexto e instrucciones para un
agente de codificación que diseñe, implemente o mantenga el sitio web
del CUEP-AP.

------------------------------------------------------------------------

## 1. Objetivo

Construir una experiencia web que traduzca la identidad de las piezas
gráficas del CUEP-AP a un sistema digital coherente, reconocible y
accesible.

La dirección visual se define como **cartelería popular contemporánea**:
una combinación de diseño editorial, comunicación de movimiento social e
ilustración popular latinoamericana.

El sitio debe transmitir:

-   Educación popular y acceso al conocimiento.
-   Organización colectiva y participación estudiantil.
-   Compromiso social y sentido comunitario.
-   Identidad universitaria independiente.
-   Juventud, energía y capacidad de convocatoria.

La interfaz no debe parecer una plantilla corporativa genérica, un
portal gubernamental ni una página institucional universitaria
convencional.

### Principio rector

> Conservar la fuerza expresiva de los carteles, pero trasladarla a una
> interfaz ordenada, legible, navegable y adaptable a distintos
> dispositivos.

------------------------------------------------------------------------

## 2. Lectura de las referencias visuales

Las piezas de referencia comparten varios rasgos:

1.  **Rojo dominante:** se utiliza en titulares, mensajes importantes y
    elementos de convocatoria.
2.  **Fondos cálidos:** predominan el marfil y las texturas de papel
    kraft.
3.  **Tipografía de impacto:** titulares grandes, condensados, pesados y
    generalmente en mayúsculas.
4.  **Contraste editorial:** combinación de tipografía sans serif
    condensada, serif de carácter editorial y sans serif funcional.
5.  **Ilustración popular:** corazón ornamental, puño levantado,
    megáfono, manos y símbolos de orientación o ubicación.
6.  **Composición de cartel:** titulares contundentes, sellos, marcos,
    recortes y sombras desplazadas.
7.  **Color complementario:** morado, turquesa y amarillo aparecen como
    acentos.

Estos rasgos deben funcionar como un lenguaje común, no como elementos
que deban aparecer todos simultáneamente en cada pantalla.

------------------------------------------------------------------------

## 3. Paleta cromática

Los siguientes valores son una **paleta inicial propuesta a partir de la
observación de las referencias**. No deben considerarse una extracción
colorimétrica exacta de los archivos originales.

### 3.1 Colores principales

  ------------------------------------------------------------------------------
  Token                  Color                      Hexadecimal Uso
  ---------------------- ---------------- --------------------- ----------------
  `--color-primary`      Rojo                         `#A92730` Titulares,
                         institucional                          botones
                                                                principales,
                                                                enlaces
                                                                destacados y
                                                                elementos de
                                                                identidad

  `--color-background`   Marfil                       `#F8F0EC` Fondo general y
                                                                superficies
                                                                principales

  `--color-paper`        Kraft                        `#CDB38B` Bloques
                                                                editoriales,
                                                                texturas y
                                                                fondos de
                                                                convocatorias

  `--color-secondary`    Morado                       `#4611A0` Acentos,
                                                                etiquetas y
                                                                llamados
                                                                secundarios

  `--color-accent`       Turquesa                     `#36C6C7` Detalles de
                                                                ilustraciones,
                                                                iconografía y
                                                                pequeños acentos
  ------------------------------------------------------------------------------

### 3.2 Colores complementarios

  -------------------------------------------------------------------------------
  Token                   Color                      Hexadecimal Uso
  ----------------------- ---------------- --------------------- ----------------
  `--color-text`          Negro carbón                 `#171313` Texto principal

  `--color-yellow`        Amarillo                     `#E8B83E` Acentos gráficos
                                                                 e ilustraciones

  `--color-red-bright`    Rojo vivo                    `#E94B48` Megáfonos,
                                                                 avisos y
                                                                 detalles
                                                                 gráficos

  `--color-paper-light`   Marfil claro                 `#FFFDFC` Tarjetas y
                                                                 superficies que
                                                                 necesiten mayor
                                                                 separación
  -------------------------------------------------------------------------------

### 3.3 Proporción orientativa

Como punto de partida para la composición general:

-   60 % fondos claros y marfil.
-   25 % rojo institucional.
-   10 % kraft y texturas.
-   5 % acentos morados, turquesas y amarillos.

No es una regla rígida. Las páginas de convocatorias pueden utilizar más
rojo o kraft que las páginas informativas.

### 3.4 Reglas de uso

-   Mantener el rojo como color de identidad y jerarquía.
-   Utilizar el morado como acento, no como sustituto del rojo.
-   Reservar el turquesa y el amarillo para detalles y recursos
    ilustrativos.
-   No colocar texto pequeño sobre texturas de papel de bajo contraste.
-   Comprobar el contraste de texto y controles conforme a WCAG 2.2 AA.
-   No comunicar estados únicamente mediante color.

------------------------------------------------------------------------

## 4. Tipografía

La identidad utiliza tres funciones tipográficas diferenciadas.

### 4.1 Tipografía de impacto

**Familia recomendada:** Anton.\
**Alternativas:** Bebas Neue u Oswald.

Uso:

-   Titulares principales.
-   Encabezados de sección.
-   Cifras y datos destacados.
-   Llamados a la acción.
-   Mensajes breves de convocatoria.

Características:

-   Preferentemente en mayúsculas.
-   Tamaños grandes y jerarquía marcada.
-   Interlineado compacto, sin comprometer la lectura.
-   Puede utilizarse una sombra desplazada en composiciones puntuales.

### 4.2 Tipografía editorial

**Familia recomendada:** Roboto Slab.\
**Alternativas:** Bitter o Zilla Slab.

Uso:

-   Manifiestos.
-   Frases institucionales.
-   Citas y declaraciones.
-   Introducciones editoriales.
-   Textos breves que requieran personalidad.

### 4.3 Tipografía funcional

**Familia recomendada:** Inter.\
**Alternativas:** DM Sans o Montserrat.

Uso:

-   Navegación.
-   Párrafos.
-   Formularios.
-   Botones.
-   Etiquetas, metadatos y textos auxiliares.

### 4.4 Reglas tipográficas

-   No utilizar la tipografía condensada en párrafos largos.
-   Evitar párrafos completos en mayúsculas.
-   Mantener una escala tipográfica consistente.
-   Usar pesos tipográficos para establecer jerarquía antes de recurrir
    a demasiados colores.
-   Cargar las familias tipográficas desde archivos locales cuando el
    proyecto lo permita; de lo contrario, utilizar una fuente web
    confiable y definir alternativas de sistema.

------------------------------------------------------------------------

## 5. Lenguaje gráfico e ilustración

Los elementos gráficos deben reforzar el concepto de educación popular y
organización colectiva.

### 5.1 Elementos característicos

  -----------------------------------------------------------------------
  Elemento                Significado visual      Uso sugerido
  ----------------------- ----------------------- -----------------------
  Corazón ornamental      Comunidad, humanidad y  Emblema, hero y piezas
                          solidaridad             destacadas

  Puño levantado          Organización y lucha    Secciones de identidad
                          colectiva               y participación

  Megáfono                Convocatoria y          Noticias, anuncios y
                          comunicación            llamados

  Papel rasgado           Materialidad artesanal  Separadores y fondos
                          y cartelería            destacados

  Sellos circulares       Identidad y pertenencia Etiquetas, distintivos
                                                  y emblemas

  Marcos geométricos      Estructura editorial    Hero, tarjetas y
                                                  composiciones

  Manos ilustradas        Participación y         Campañas y
                          comunidad               convocatorias

  Sombras desplazadas     Estética de cartel      Titulares y elementos
                          impreso                 seleccionados
  -----------------------------------------------------------------------

### 5.2 Tratamiento visual

-   Priorizar ilustraciones vectoriales o recursos gráficos de
    apariencia artesanal.
-   Favorecer colores sólidos, contornos definidos y formas
    reconocibles.
-   Mantener una estética coherente entre ilustraciones de distintas
    secciones.
-   Evitar mezclar ilustraciones 3D, fotografías de stock corporativas y
    dibujos populares sin una dirección de arte común.
-   Utilizar los emblemas originales del colectivo cuando estén
    disponibles.
-   No recrear ni alterar logotipos oficiales mediante aproximaciones
    generadas automáticamente.

### 5.3 Texturas

La textura kraft debe utilizarse de manera selectiva:

-   Fondos de convocatorias.
-   Separadores de secciones.
-   Bloques editoriales destacados.
-   Detalles decorativos del hero.

No utilizar una textura ruidosa como fondo permanente de todo el sitio.
El contenido debe conservar suficiente contraste y espacio visual.

------------------------------------------------------------------------

## 6. Dirección de arte para la interfaz

La dirección recomendada combina:

-   **70 % diseño editorial contemporáneo.**
-   **20 % cartelería de movimiento social.**
-   **10 % ilustración popular latinoamericana.**

Estos porcentajes son una orientación conceptual, no una medición
literal de superficie o componentes.

### 6.1 Sensación general

El sitio debe sentirse:

-   Expresivo, pero no desordenado.
-   Popular, pero no improvisado.
-   Institucional, pero no burocrático.
-   Juvenil, pero no infantil.
-   Gráfico, pero no saturado.
-   Accesible y fácil de utilizar.

### 6.2 Espacio y composición

-   Utilizar márgenes generosos en secciones informativas.
-   Reservar las composiciones densas para carteles, convocatorias y
    bloques de campaña.
-   Alternar secciones claras con bloques de color.
-   Evitar que todas las tarjetas tengan la misma composición si el
    contenido requiere jerarquías distintas.
-   Mantener una cuadrícula consistente y alineaciones claras.
-   Utilizar bordes definidos y radios moderados.

------------------------------------------------------------------------

## 7. Arquitectura visual sugerida para el sitio

La siguiente estructura es una propuesta inicial. El agente debe
adaptarla a las necesidades reales del proyecto y a las páginas que
existan en el repositorio.

### 7.1 Encabezado y navegación

Características:

-   Fondo marfil o blanco cálido.
-   Logotipo del colectivo a la izquierda.
-   Navegación sencilla y legible.
-   Enlaces con estados hover y focus claramente visibles.
-   Botón destacado para participar, registrarse o consultar
    convocatorias.
-   Menú móvil accesible mediante teclado y tecnologías de asistencia.

No convertir la navegación en un cartel: su prioridad es la usabilidad.

### 7.2 Hero principal

Debe ser la sección de mayor impacto visual.

Elementos sugeridos:

-   Titular grande en Anton.
-   Frase institucional o mensaje de convocatoria.
-   Uno o dos botones con acciones claras.
-   Emblema o ilustración ornamental.
-   Fondo marfil con una textura kraft parcial o un bloque rojo.
-   Composición asimétrica inspirada en los carteles.

Evitar colocar demasiado texto dentro de la imagen. Los titulares y
botones deben ser HTML real para conservar accesibilidad, indexación y
adaptación responsive.

### 7.3 Quiénes somos

-   Presentación breve del colectivo.
-   Manifiesto o declaración de principios.
-   Valores y objetivos.
-   Ilustraciones pequeñas o sellos gráficos.
-   Tipografía editorial para frases destacadas.

### 7.4 Nuestras sedes

-   Tarjetas con nombre, ubicación, descripción y fotografía cuando
    exista.
-   Acciones claras para consultar información o llegar a cada sede.
-   Posibilidad de incorporar mapas si el proyecto lo requiere.
-   No usar ilustraciones decorativas en lugar de información geográfica
    real.

### 7.5 Cursos y convocatorias

Esta sección puede recuperar con mayor intensidad el lenguaje de los
carteles:

-   Títulos grandes.
-   Etiquetas de estado o fechas.
-   Fondos kraft y acentos morados.
-   Información de inscripción claramente jerarquizada.
-   Botones visibles.
-   Carteles originales como imágenes complementarias, nunca como única
    fuente de información.

### 7.6 Noticias y actividades

-   Diseño editorial tipo revista.
-   Imágenes con proporciones consistentes.
-   Fechas y categorías visibles.
-   Titulares de lectura sencilla.
-   Composiciones especiales para campañas relevantes.

### 7.7 Participa y contacto

-   Mensajes directos y convocantes.
-   Formularios simples.
-   Botones de acción destacados.
-   Información de contacto legible.
-   Indicaciones claras de privacidad y tratamiento de datos cuando
    corresponda.

### 7.8 Footer

-   Fondo rojo institucional o negro carbón.
-   Logotipo y descripción breve.
-   Enlaces principales.
-   Redes sociales.
-   Datos de contacto.
-   Créditos y avisos legales aplicables.

------------------------------------------------------------------------

## 8. Componentes y patrones reutilizables

El agente debe implementar la identidad como un sistema de componentes,
no como estilos aislados en cada página.

Componentes sugeridos:

  Componente         Características
  ------------------ ---------------------------------------------------
  `SiteHeader`       Navegación limpia, logotipo y CTA
  `HeroSection`      Titular de impacto, texto, acciones e ilustración
  `SectionHeading`   Título condensado y posible subtítulo editorial
  `PaperSection`     Sección con fondo kraft o textura
  `LocationCard`     Tarjeta de sede con información y acción
  `CourseCard`       Curso, fechas, modalidad y estado
  `NewsCard`         Imagen, categoría, fecha y titular
  `PosterFrame`      Contenedor para carteles originales
  `CallToAction`     Bloque de convocatoria
  `SiteFooter`       Identidad, navegación secundaria y contacto

### 8.1 Botones

**Primario**

-   Fondo rojo institucional.
-   Texto claro.
-   Peso tipográfico alto.
-   Bordes moderadamente redondeados.
-   Estados hover, focus, active y disabled.

**Secundario**

-   Fondo transparente o marfil.
-   Borde rojo o morado.
-   Texto con contraste suficiente.

**Enlace textual**

-   Color rojo o morado según el contexto.
-   Subrayado o indicador visual en hover.
-   Foco visible al navegar con teclado.

### 8.2 Tarjetas

-   Fondo marfil claro o blanco cálido.
-   Borde fino o sombra desplazada discreta.
-   Radio moderado.
-   Título en tipografía de impacto, sin abusar del tamaño.
-   Información funcional en Inter.
-   Ilustración o textura únicamente cuando aporte significado.

### 8.3 Etiquetas

Usar etiquetas para categorías, estados, fechas y tipos de convocatoria.
Mantenerlas pequeñas, legibles y con contraste adecuado.

------------------------------------------------------------------------

## 9. Tokens CSS iniciales

El siguiente bloque puede servir como punto de partida. El agente debe
integrarlo en la arquitectura de estilos existente, evitando duplicar
variables o crear sistemas paralelos.

``` css
:root {
  /* Identidad cromática */
  --color-primary: #A92730;
  --color-secondary: #4611A0;
  --color-background: #F8F0EC;
  --color-paper: #CDB38B;
  --color-accent: #36C6C7;
  --color-text: #171313;
  --color-yellow: #E8B83E;
  --color-red-bright: #E94B48;
  --color-surface: #FFFDFC;

  /* Tipografía */
  --font-display: "Anton", Impact, sans-serif;
  --font-editorial: "Roboto Slab", Georgia, serif;
  --font-body: "Inter", Arial, sans-serif;

  /* Bordes y sombras */
  --radius-card: 8px;
  --radius-button: 4px;
  --border-default: 1px solid var(--color-primary);
  --shadow-poster: 6px 6px 0 #DDBFC0;

  /* Espaciado */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-12: 3rem;
  --space-16: 4rem;

  /* Contenido */
  --content-max-width: 1200px;
  --page-gutter: clamp(1rem, 4vw, 3rem);
}

body {
  margin: 0;
  background: var(--color-background);
  color: var(--color-text);
  font-family: var(--font-body);
}

h1,
h2,
h3,
.display-title {
  font-family: var(--font-display);
  color: var(--color-primary);
  text-transform: uppercase;
  line-height: 0.98;
}

.editorial-text {
  font-family: var(--font-editorial);
}

.container-site {
  width: min(
    calc(100% - 2 * var(--page-gutter)),
    var(--content-max-width)
  );
  margin-inline: auto;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.8rem 1.25rem;
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-button);
  background: var(--color-primary);
  color: #fff;
  font-family: var(--font-body);
  font-weight: 700;
  text-decoration: none;
  transition: background-color 160ms ease,
              transform 160ms ease;
}

.btn-primary:hover {
  background: #851F27;
  border-color: #851F27;
}

.btn-primary:focus-visible,
a:focus-visible,
button:focus-visible,
input:focus-visible,
textarea:focus-visible,
select:focus-visible {
  outline: 3px solid var(--color-secondary);
  outline-offset: 3px;
}

.poster-shadow {
  box-shadow: var(--shadow-poster);
}

.paper-surface {
  background-color: var(--color-paper);
}
```

### 9.1 Consideraciones sobre el CSS

-   No aplicar `text-transform: uppercase` globalmente a todos los
    encabezados si afecta la lectura o el contenido.
-   No usar sombras decorativas en todos los componentes.
-   Mantener los estilos de foco visibles.
-   Comprobar que las combinaciones de colores cumplan los criterios de
    contraste.
-   Respetar `prefers-reduced-motion` cuando se agreguen transiciones o
    animaciones.
-   Evitar selectores globales que interfieran con Bootstrap o con
    componentes de terceros.

------------------------------------------------------------------------

## 10. Responsive design

La identidad debe conservarse en escritorio, tablet y móvil.

### Escritorio

-   Hero con composición asimétrica.
-   Titulares grandes.
-   Ilustraciones ornamentales visibles.
-   Cuadrículas de dos, tres o cuatro columnas según el contenido.

### Tablet

-   Reducir la escala de titulares.
-   Ajustar columnas y márgenes.
-   Evitar que las ilustraciones compitan con el contenido.

### Móvil

-   Una columna para el contenido principal.
-   Titulares condensados con tamaño fluido.
-   Botones cómodos para interacción táctil.
-   Navegación móvil funcional y accesible.
-   Texturas y elementos decorativos simplificados.
-   Evitar desbordamientos horizontales.
-   No convertir los textos en imágenes.

Usar herramientas fluidas como `clamp()`, Grid y Flexbox en lugar de
depender exclusivamente de anchos fijos.

------------------------------------------------------------------------

## 11. Accesibilidad y calidad

La identidad visual nunca debe prevalecer sobre la comprensión del
contenido.

Requisitos mínimos:

1.  Contraste conforme a WCAG 2.2 AA.
2.  Navegación completa por teclado.
3.  Indicadores de foco visibles.
4.  HTML semántico.
5.  Jerarquía correcta de encabezados.
6.  Textos alternativos para imágenes informativas.
7.  Imágenes decorativas con alternativa vacía (`alt=""`) cuando
    corresponda.
8.  Formularios con etiquetas asociadas y mensajes de error
    comprensibles.
9.  Controles táctiles de tamaño suficiente.
10. Respeto a las preferencias de movimiento reducido.
11. Contenido textual real y seleccionable.
12. No depender exclusivamente del color para comunicar información.

------------------------------------------------------------------------

## 12. Reglas para fotografías y recursos gráficos

-   Priorizar fotografías reales de sedes, actividades, cursos y
    comunidad cuando estén disponibles y exista autorización para
    utilizarlas.
-   No sustituir fotografías documentales por imágenes genéricas de
    stock.
-   No inventar personas, sedes, eventos, logotipos ni actividades.
-   Mantener proporciones de imagen consistentes dentro de cada tipo de
    tarjeta.
-   Optimizar peso y formato de los recursos.
-   Utilizar imágenes de alta calidad para carteles y emblemas.
-   Conservar los archivos originales de identidad y no sobrescribirlos.
-   Si falta un recurso, utilizar un placeholder coherente y claramente
    identificable, no una imagen que simule ser documental.

------------------------------------------------------------------------

## 13. Instrucciones operativas para el agente de codificación

Estas instrucciones deben tratarse como criterios de implementación.

### 13.1 Antes de modificar el proyecto

1.  Inspeccionar la estructura del repositorio.
2.  Identificar framework, versión, sistema de estilos y dependencias.
3.  Revisar componentes, layouts y convenciones ya existentes.
4.  Localizar logotipos, carteles, fotografías, iconos y fuentes
    proporcionados.
5.  Identificar las páginas y funcionalidades existentes.
6.  No reemplazar tecnologías ni reestructurar el proyecto sin
    necesidad.

### 13.2 Durante la implementación

1.  Definir los tokens cromáticos y tipográficos en un punto central.
2.  Crear o adaptar componentes reutilizables.
3.  Aplicar la identidad por capas: estructura, tipografía, color,
    ilustración y textura.
4.  Mantener separada la presentación del contenido cuando la
    arquitectura lo permita.
5.  Reutilizar el sistema de componentes y estilos existente.
6.  Implementar estados hover, focus, active y disabled.
7.  Probar el diseño en distintos anchos de pantalla.
8.  Optimizar imágenes y recursos.
9.  Mantener las funcionalidades existentes.
10. Evitar código duplicado y reglas CSS excesivamente específicas.

### 13.3 Restricciones

El agente no debe:

-   Convertir todo el sitio en un cartel saturado.
-   Utilizar texturas kraft en todas las secciones.
-   Aplicar tipografías display a párrafos extensos.
-   Inventar contenido institucional.
-   Alterar el significado de los emblemas.
-   Crear botones que no tengan una acción funcional.
-   Utilizar texto incrustado en imágenes como sustituto de contenido
    HTML.
-   Eliminar funcionalidades existentes para simplificar el diseño.
-   Incorporar dependencias innecesarias.
-   Cambiar el stack tecnológico sin autorización.

### 13.4 Al terminar cada tarea

Verificar:

-   Consistencia cromática y tipográfica.
-   Adaptación responsive.
-   Funcionamiento de enlaces y botones.
-   Navegación por teclado.
-   Contraste y legibilidad.
-   Consola del navegador y errores de ejecución.
-   Integridad de las funcionalidades existentes.

------------------------------------------------------------------------

## 14. Criterios de aceptación visual

Una implementación puede considerarse alineada con esta guía cuando:

-   El rojo institucional y los fondos cálidos son reconocibles.
-   Los titulares tienen carácter de cartelería y una jerarquía clara.
-   El corazón ornamental y otros recursos gráficos se utilizan con
    coherencia.
-   Las texturas están presentes de manera selectiva.
-   La interfaz tiene suficiente espacio visual y no se percibe
    saturada.
-   Las secciones informativas son fáciles de leer.
-   Las convocatorias conservan la energía visual de los carteles.
-   El sitio funciona correctamente en móvil y escritorio.
-   La identidad es consistente entre páginas y componentes.
-   La accesibilidad y la funcionalidad no se sacrifican por motivos
    estéticos.

------------------------------------------------------------------------

## 15. Prompt base para el agente de codificación

El siguiente texto puede copiarse como instrucción inicial o
incorporarse a un archivo de contexto del agente:

> Implementa y mantén la identidad gráfica del Colectivo Universitario
> por la Educación Popular (CUEP-AP) siguiendo esta guía.
>
> La dirección visual es cartelería popular contemporánea: diseño
> editorial, comunicación de movimiento social e ilustración popular
> latinoamericana. La paleta se basa en rojo `#A92730`, marfil
> `#F8F0EC`, kraft `#CDB38B`, morado `#4611A0` y turquesa `#36C6C7`.
> Utiliza Anton para titulares, Roboto Slab para recursos editoriales e
> Inter para contenido funcional.
>
> Integra el corazón ornamental, el puño levantado, el megáfono, los
> sellos y las texturas de papel como recursos gráficos coherentes. No
> satures la interfaz: prioriza una composición editorial clara, con
> espacios en blanco, navegación intuitiva y componentes reutilizables.
>
> Antes de modificar código, inspecciona el repositorio y respeta su
> stack, arquitectura, dependencias y convenciones. No inventes
> contenido, fotografías, logotipos ni información institucional. No
> elimines funcionalidades existentes.
>
> Implementa una experiencia responsive y accesible, con HTML semántico,
> navegación por teclado, estados de interacción visibles y contraste
> WCAG 2.2 AA. Utiliza esta guía como referencia visual y técnica
> durante todas las tareas relacionadas con el sitio.

------------------------------------------------------------------------

## 16. Nota de evolución

Esta guía constituye una primera definición del sistema visual a partir
de tres piezas gráficas. Para consolidar una identidad institucional
definitiva conviene incorporar posteriormente:

-   Archivos vectoriales oficiales de los logotipos y emblemas.
-   Valores cromáticos obtenidos de los archivos originales.
-   Archivos tipográficos y licencias correspondientes.
-   Manual de uso de marca, si existe.
-   Fotografías institucionales autorizadas.
-   Ejemplos de aplicaciones adicionales: publicaciones, presentaciones,
    señalética y materiales impresos.

Hasta contar con esos recursos, los valores y componentes aquí descritos
deben tratarse como una **propuesta de dirección de arte**, no como un
manual oficial de marca.
