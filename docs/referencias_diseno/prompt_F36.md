# F36 · Rediseño de Ética y límites y de Ayuda y glosario

Eres el asistente de código del repositorio `waymo-evaluacion` (app Streamlit «Lente», EP3). Esta tarea rediseña dos páginas de texto: **Ética y límites** y **Ayuda y glosario**. Es trabajo de presentación. Trabaja las dos partes en orden (Ética y luego Ayuda) sin esperar mi respuesta entre una y otra, pero si alguna regla de abajo se rompe, detente y repórtalo. Tengo hasta el mediodía, así que prioriza terminar lo esencial y reporta lo que quede.

Esta tarea va después de F31 a F35. No las rehagas ni las modifiques. Si alguna no está aplicada, no la apliques aquí: anótalo en el reporte.

## 0 · Material de referencia

Copia `f36_etica_ayuda_propuesta.html` a `docs/referencias_diseno/` y ábrelo en el navegador antes de empezar. El menú lateral cambia entre las dos páginas. Arriba del marco hay dos botones, «Local (hoy)» y «Publicada en internet», que son **solo de la maqueta**: muestran cómo cambiarían tres textos según el despliegue (ver sección 3).

- **Gana el HTML** en jerarquía, orden de bloques y comportamiento. Si este prompt y el HTML se contradicen, sigue el HTML, salvo en los puntos marcados con **«Ojo»**.
- No copies el CSS tal cual. Usa el tema oscuro y los componentes de la app, y llega al mismo resultado visual.
- Los iconos de la maqueta son SVG simples. Usa los que ofrezca la app o un SVG equivalente; no agregues dependencias nuevas.

## 1 · Reglas

1. **No tocar** el modelo, los datos, los umbrales, los resultados guardados ni ninguna cifra. La solución v3 congelada (sello del 2026-11-14) debe seguir intacta: verifica que su sello no cambia.
2. **No hagas commit.** No despliegues nada ni abras conexiones a internet.
3. **Antes de editar**, imprime la lista de archivos que vas a tocar. Después sigue sin esperar.
4. **Antes de empezar, captura el estado actual** de las dos páginas, y guarda en un archivo temporal fuera del repo **todos los textos que muestran hoy**: párrafos, definiciones del glosario, preguntas y respuestas de las preguntas frecuentes, y las frases de «Uso». Sirven para la regresión de textos (regla 6). **Las respuestas de las preguntas frecuentes nunca las he visto**, así que tu captura es la única fuente.
5. **Pruebas:** corre la suite completa antes y después de cada parte y anota los conteos. Si una prueba que pasaba falla, detente.
6. **Regresión de textos:** cada frase que hoy existe en estas dos páginas debe seguir existiendo en alguna parte, con la misma redacción, salvo las excepciones de este prompt. Escribe una prueba que lo verifique con tus textos guardados. Los únicos cambios permitidos son de orden, de formato y los ajustes mínimos de redacción que pida una frase partida en dos.
7. **Cifras:** 0,823, 79,8 %, 61,9 %, 80,6 %, 44,3 % y «115 casos en 14 segmentos» deben salir de las mismas funciones que usan Validación y el Resumen. Si hoy están escritas a mano en el texto, pásalas a esas funciones. Si no se puede, déjalas como están y repórtalo.
8. **Accesibilidad:** contraste ≥ 4,5:1, tamaño mínimo 12 px, foco visible solo con teclado, el estado nunca solo por color (la barra de peatones/ciclistas lleva el número escrito), iconos decorativos con `aria-hidden`, la barra de comparación con descripción de texto.
9. **Lenguaje:** español, sin jerga. Conserva el pie de página de Waymo y la línea «Solución v3 congelada…».

---

## PARTE A · Ética y límites

**Qué es la página:** la ficha del sistema. Su mensaje más importante es que decide siempre una persona.

**Cambios (sigue la maqueta):**

1. **Bloque superior «Decide siempre una persona»**, grande, con icono y dos avisos al lado: «Nunca debe usarse para descartar cajas sin revisarlas» y «No es una prueba de seguridad del vehículo. Mide si una caja 3D tiene pareja 2D, no si el peatón fue bien detectado.» Estas frases salen del párrafo actual de «Propósito»: se mudan aquí y **no se duplican** en Propósito.
2. **Propósito** queda con la frase que explica qué hace: ordenar las cajas 3D de peatones y ciclistas para que una persona revise primero las que más probablemente no tienen su par 2D de cámara, y avisar qué cámaras tienen huecos.
3. **Datos y licencia** como lista de tres puntos (Waymo Open Dataset v2 con 41 segmentos de desarrollo; uso no comercial y sin redistribución; trabajo académico, curso MLY1101). El número de segmentos sale de la app, no escrito a mano.
4. **Desempeño:** tres tarjetas (AUC, recall en el punto A, cajas sin pareja que se encuentran al revisar el 20 %), la etiqueta «en muestra» junto al título, la frase actual de «Todas las cifras son en muestra…» y un enlace a Validación.
5. **Límites conocidos:** barra de comparación peatones/ciclistas con los dos porcentajes escritos, la línea «ciclistas: N casos en M segmentos» y los dos puntos actuales (más segmentos de día que de noche y tres ubicaciones; un hueco es una hipótesis, los hallazgos post hoc son hipótesis).
6. **Consideraciones éticas** y **Dónde corre** en dos tarjetas iguales, una al lado de la otra, con su icono. **Ojo:** el contenido de estas dos tarjetas depende del modo de despliegue (sección 3).

---

## PARTE B · Ayuda y glosario

**Cambios (sigue la maqueta):**

1. **«Cómo funciona, en tres pasos»:** tres tarjetas numeradas con flechas (detector de huecos, cola de cajas, una persona decide). El texto de cada una sale del «Flujo de tres capas» actual, partido en tres. Cada tarjeta lleva un enlace a la página que corresponde (Auditoría de cámaras, Cola de revisión, Ética y límites). Verifica que los enlaces funcionan con la navegación de la app.
2. **«Qué hace cada página»:** tarjetas con una línea por página. Las tres actuales (Rol, Auditoría de cámaras, Cola de revisión) conservan **su texto actual palabra por palabra**. Se agregan tres: Validación, Explica una caja y Puntuar datos nuevos. Para estas tres usa el subtítulo que hoy tiene cada página en la app. Si una de esas páginas no está rediseñada todavía, usa su subtítulo actual.
   **Ojo:** verifica que cada línea sigue siendo verdad después de F31 a F35. Por ejemplo, la línea de Cola de revisión dice que se elige el segmento, el flujo y el presupuesto; si tras F32 los filtros cambiaron, ajusta la frase mínimamente y dímelo. Verifica también «El rol cambia la página que se abre».
3. **Glosario con buscador y grupos.** Tarjetas en vez de tabla. Las 11 definiciones actuales, **palabra por palabra**, con estos grupos: **Datos** (Caja, Par 2D, Celda, Hueco), **Revisión** (Cola, Presupuesto, Cobertura), **Rigor** (Intervalo de confianza, Post hoc, En muestra, Sin prueba ciega). Si el glosario actual tiene más términos que esos 11, inclúyelos, asígnales un grupo y dime cuáles. El buscador filtra por término y por definición, sin distinguir mayúsculas ni tildes si es simple de hacer. Los botones de grupo filtran por grupo, y «Todos» los muestra todos. Si no hay coincidencias: «Ningún término coincide con la búsqueda.»
4. **Preguntas frecuentes:** se mantienen como desplegables con **las preguntas y respuestas actuales**, sin cambiar el texto. **Ojo:** la respuesta a «¿Se guardan o se envían los archivos?» depende del modo de despliegue (sección 3).

---

## 3 · Modo de despliegue (importante)

Tengo previsto desplegar la app esta tarde. Hoy varios textos dicen que la app corre solo en este equipo y que no hay conexión a internet. Si la app se publica, esas frases dejarían de ser ciertas.

1. Crea **una sola constante de configuración** (por ejemplo `MODO_DESPLIEGUE`, con los valores `"local"` y `"publicado"`) y haz que estos textos la lean desde **un único lugar**:
   - «Consideraciones éticas» (Parte A).
   - «Dónde corre» (Parte A).
   - La respuesta de «¿Se guardan o se envían los archivos?» (Parte B).
   - Las etiquetas de la página Puntuar datos nuevos («Procesamiento local y en memoria», «No se guarda nada»), si F35 está aplicada.
2. **El valor por defecto es `"local"`**, con los textos actuales palabra por palabra. **No actives `"publicado"`.** Implementa su variante con los borradores de la maqueta (botón «Publicada en internet») para que yo pueda cambiarlo después de decidir cómo se despliega. Los borradores de la maqueta están marcados «borrador: verificar» y tienen un hueco `[nombre del servicio]`.
3. **Verifica en el código y dime en el reporte, con evidencia:**
   - ¿Los archivos subidos en Puntuar datos nuevos se escriben a disco, a un caché persistente, a logs o a una carpeta temporal? ¿Se usa `st.cache_data`, `st.cache_resource` o similar con datos del usuario?
   - ¿La aplicación escribe algo fuera de memoria durante una sesión?
   - ¿Qué archivos de datos, tablas derivadas o resultados guardados formarían parte de un despliegue (la carpeta que se publicaría)? Lista los archivos con su tamaño.
   - ¿Hay datos del Waymo Open Dataset dentro de esa carpeta? Recuerda que el pie de página dice que son de uso no comercial y que sus datos no se redistribuyen. **No decidas tú si se pueden publicar: lista qué hay y yo reviso la licencia.**
   - ¿Hay rutas, nombres de usuario del equipo o credenciales en archivos que se publicarían?
4. **No cambies** ninguna de esas respuestas en el código: solo repórtalas.

---

## 4 · Pruebas específicas

- Regresión de textos (regla 6): todas las frases actuales siguen presentes, y las 11 definiciones y las respuestas de las preguntas frecuentes son idénticas a las de antes.
- Buscador del glosario: por término, por parte de una definición, por grupo, combinando grupo y búsqueda, y sin resultados.
- Cada uno de los tres textos de la sección 3 cambia con la constante, y por defecto salen los textos actuales.
- Los enlaces de los tres pasos llegan a la página correcta.
- Las cifras de la Parte A coinciden con las de Validación y el Resumen.

## 5 · Entrega

1. **Carpeta de revisión** `images/ep3/pagina/para_revision_f36/`, con capturas a 1366 px, **máximo 8 PNG**: `f36_01_etica_arriba.png`, `f36_02_etica_abajo.png`, `f36_03_etica_modo_publicado.png` (activando la constante solo para la captura y volviendo a `"local"` después), `f36_04_ayuda_tres_pasos.png`, `f36_05_ayuda_glosario.png`, `f36_06_ayuda_busqueda.png`, `f36_07_ayuda_preguntas_abiertas.png`.
2. **`REPORTE_F36.md`** en esa carpeta, **sin límite de largo**: qué cambió por parte, qué no pudiste hacer, en qué te apartaste de la maqueta y por qué, las decisiones que tomaste, los resultados de la verificación de la sección 3 con evidencia, las respuestas actuales de las preguntas frecuentes (para que yo las vea), los términos extra del glosario si los hubo, las frases que ajustaste para que siguieran siendo ciertas, los conteos de pruebas antes y después, y las cifras que pasaste a funciones compartidas.
3. **`estado_git.txt`** en esa carpeta, con la salida de `git status --short`.
4. Resume en tu respuesta final **en 10 líneas**: qué quedó hecho, qué no, y lo que debo decidir yo.

## 6 · Solo reporta, no cambies

Cualquier mención del Modo presentación, de pestañas antiguas de Validación («Hiperparámetros», «Ensambles», «Selección», «No supervisado») o del término «Lista A» en textos de la app; y cualquier página que diga que la app corre solo en local y no esté en la lista de la sección 3.
