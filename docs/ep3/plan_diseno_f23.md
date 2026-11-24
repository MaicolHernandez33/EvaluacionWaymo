# Plan de diseño de F23 (rediseño estructural de la página)

*Generado por `scripts/ep3/generar_plan_diseno_f23.py`. Se escribió antes de cambiar el código; el informe de lo que se hizo y lo que no está en `REPORTE_F23.md`.*

> **Nota de F24.** Esta es la intención de F23 y queda como historia: F24 cambió la piel (tema oscuro tipo consola de control, una sola familia sans) sin tocar la estructura ni el contenido. La paleta, la tipografía y los radios de abajo son los de F23; los tokens vigentes están en `app/estilos.py` y en `guia_estilo_pagina.md`.

**Objetivo.** Que la página parezca un producto de revisión y no una plantilla: se cambia la estructura (qué va primero, qué se agrupa, qué se quita), no solo los colores. Decide siempre una persona; el diseño solo ordena lo que ella necesita ver.

**Tema y público.** Auditor de etiquetas 3D: una persona revisa cajas 3D (LiDAR) de peatones y ciclistas sin par 2D de cámara. Trabaja sentada, con tablas, y necesita saber qué cámara falla antes de abrir una caja. Eso decide la pieza memorable.

## Color
Seis valores con nombre. Se mantienen el cobalto como acción, el teal para la celda sana, el rojo para el hueco y el ámbar para «en muestra».

| Nombre | Valor | Rol |
|---|---|---|
| Papel | `#F8F9FB` | lienzo de la página y barra lateral (el mismo tono; las separa una línea fina) |
| Tinta | `#14202F` | texto principal; el texto secundario es `#4B586B` |
| Cobalto | `#2457D6` | la acción: enlaces, selección, ítem activo, cámara activa del anillo, barras de datos |
| Teal sano | `#0B6B74` | celda sana: escala del mapa de calor y cuña sana del anillo (claro `#A9D3D7`) |
| Rojo hueco | `#B42318` | solo hueco de cámara, siempre con una «X» y con texto |
| Ámbar en muestra | `#C98A00` | solo la etiqueta «en muestra» y el chip de estado (texto `#5C3D00` sobre `#FFF4D6`) |

Neutros de apoyo: superficie de controles y encabezados `#EEF1F5`, borde `#D8DEE7`, panel principal blanco `#FFFFFF`. **Sin datos:** `#E3E6EB`, gris plano y neutro: «sin datos» no es una alerta, así que no lleva rayado, rojo ni teal. La barra lateral pasa a tono claro (Papel) con una línea fina de separación; desaparece la tinta oscura y con ella el acento azul sobre fondo oscuro.

Mapa de calor y anillo usan **los mismos tres estados**: sana (teal), hueco (rojo con «X») y sin datos (gris plano). La leyenda de la Auditoría y la del Resumen dicen lo mismo con las mismas palabras.

## Tipografía
Dos familias, con roles distintos, **ambas del sistema** (sin `@font-face`, sin CDN, sin Google Fonts, sin archivos externos: la página funciona sin internet).

| Rol | Familia | Dónde |
|---|---|---|
| Voz editorial | `Cambria, "Palatino Linotype", "Book Antiqua", Georgia, serif` | títulos de página, la afirmación del Resumen y el título de los paneles |
| Interfaz y datos | `"Segoe UI Variable Text", "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif` | todo lo demás; cifras tabulares |

*Por qué un serif.* La afirmación del Resumen es una frase con cifras, y una frase se lee mejor con un serif de texto que con otro sans de panel. Se eligió **Cambria** porque viene con Windows (y con Office en Mac) y tiene cifras de caja alta; Georgia, que se probó primero, tiene cifras de caja baja que desordenan una frase con «80.571» y «41». Si Cambria falta, caen Palatino y Georgia: la jerarquía se mantiene.

Escala (base 15 px; modo presentación multiplica por 1,18): nota 0,78 rem; secundario 0,86; cuerpo 1; destacado 1,12; título de panel 1,25; título de página 1,75; afirmación 1,95. Más de dos pesos solo en la afirmación (400 y 700). Interlineado 1,25 en serif grande y 1,5 en cuerpo; líneas de menos de 75 caracteres.

## Layout
**Dónde está la pieza memorable:** el anillo de cámaras (`anillo_camaras`) es el protagonista del Resumen y reaparece, más pequeño, en el detalle de la cola y en la Auditoría. Todo lo demás se mantiene sobrio.

### Resumen
```
 Resumen                                                   [Datos de desarrollo ▾]
 Estado de las etiquetas 2D de peatones y ciclistas en 41 segmentos de desarrollo.
 +----------------------------------------------------------------------------+
 |  En la muestra de 41 segmentos, el detector        .-'''-.                 |
 |  marca 2 celdas segmento × cámara como           2 /  1  \ 3   anillo       |
 |  posibles huecos de cámara. [en muestra]          |  [=] |  grande,        |
 |                                                  4 \     / 5 5 cámaras      |
 |  Segmento [ ...534050  v ]                         '-...-'                 |
 |                                                  Sana  Hueco  Sin datos    |
 +----------------------------------------------------------------------------+   <- único panel elevado
 Cifras de apoyo                       Alertas
 ---------------------------------     --------------------------------------
 Cajas analizadas        80.571        Ciclistas: regla poco confiable   Ética
 Cajas sin pareja        21,2 %        Celdas marcadas                   Auditoría
 AUC (validación cruz.)  0,823         Validación externa pendiente      Validación
 Horas para el 80 %  ... barras en la tabla
```
Se quitan las cuatro fichas de indicadores y el gráfico de barras; las horas pasan a una tabla pequeña con una barra fina en cada fila. A 1366 × 768 se ven completos el anillo y la afirmación, sin desplazarse.

### Cola de revisión
```
 Cola de revisión                                          [Datos de desarrollo ▾]
 Segmento [v]  Flujo [v]  Modo (o) Presupuesto ( ) Meta  Presupuesto ----o--  [Volver a 20 %]
 ------------------------------------------------------------------------------
 Con auditoría previa: unas 70 de cada 100 ... (frase del resultado, sin caja)
 [ Curva de priorización ]  Cola de cajas
 +---------------------------------------------+  +---------------------------+
 | Prioridad | Prob. | Segmento | Cámara |     |  |  .-'-.   Seleccione una   |
 | Puntos sup. | Tipo de caso                  |  |  anillo  fila para ver su |
 | 1  87,8 %  ...534050  1 (frontal) ...       |  |  apagado detalle          |
 +---------------------------------------------+  +---------------------------+
   6 columnas, sin recortes, radio 0                panel siempre visible
```
Seis columnas que sirven para decidir: prioridad, probabilidad de no tener pareja, segmento, cámara, puntos del sensor superior y tipo de caso. Fotogramas, distancia, clase e identificadores pasan al panel de detalle. La curva de priorización es la primera pestaña.

### Auditoría de cámaras
```
 Auditoría de cámaras                                      [Datos de desarrollo ▾]
 Grupo [v]  Orden [v]  [ ] Solo celdas con datos       Segmentos | Celdas | Cajas | Sin pareja
 Leyenda: Sana (teal) / Hueco (rojo y X) / Sin datos (gris plano)  --------------------------
 +------------------------------+                    anillo pequeño + Lista A (tabla, radio 0)
 | mapa de calor 5 cámaras      |
 | gris plano = sin datos       |
 +------------------------------+
```

## Revisión contra los defaults
Pregunta aplicada a cada parte: *¿se vería igual en cualquier panel de SaaS?* Si sí, se rehizo.

| Parte | Primer borrador | Por qué era genérico | Qué se cambió |
|---|---|---|---|
| Resumen | cuatro fichas de indicadores y, debajo, un gráfico | el mosaico de números grandes es lo primero que se ve en cualquier panel | una afirmación con cifras reales y el anillo; las cifras de apoyo van en una tabla pequeña |
| Superficies | todo en tarjetas con el mismo radio y la misma sombra | ninguna jerarquía: todo pesa igual | un solo tipo de panel elevado (radio 14 px, sombra suave) para lo principal; controles de 6 px; tablas de 0 px; lo demás, línea fina y espacio |
| Barra lateral | tinta oscura con acento azul claro | es la barra lateral de plantilla por excelencia | tono Papel, igual que el lienzo, con una línea fina; el ítem activo en cobalto suave |
| Tipografía | un sans para todo | la página no tenía voz | serif del sistema para títulos y afirmación; sans para datos |
| Indicadores | glifo decorativo dentro de cada ficha | adorno sin información | se quita; la tira de cifras de Auditoría y Puntuar es una fila con líneas finas |
| Estado «sin datos» | gris con rayado diagonal | el rayado llama la atención como una alerta | gris plano y neutro; solo el hueco usa rojo |
| Enlaces de alertas | flecha antes del nombre de la página | flecha de plantilla | solo el texto del enlace |
| Pie y versión | cadenas unidas con puntos medios | rasgo de plantilla | frases separadas por punto |
| Curvas | color y trazo; XGBoost y regla casi iguales en color | se distinguían solo por el trazo | paleta validada (abajo) |

## Paleta de curvas (dataviz)
Se validó con `validate_palette.js` en modo claro (superficie = Papel): meta de separación para daltonismo (ΔE de CVD) de 8 o más y piso de visión normal de 15 o más entre curvas adyacentes. Resultados y números en `REPORTE_F23.md` y en `f23_paleta_validacion.json`. Ninguna curva pinta texto con su color: la leyenda usa el trazo y el texto va en tinta.

| Curva | Antes | Después |
|---|---|---|
| Dos pasos | `#2457D6` | `#2457D6` |
| Un paso | `#B45309` | `#B45309` |
| Regla de puntos, un paso | `#6B7280` | `#1C9B84` |
| XGBoost (referencia) | `#0B6E69` | `#8F81E8` |
| Ensamble E2 (referencia) | `#7C3AED` | `#844A83` |

## Fuera de alcance
Páginas nuevas, roles nuevos, monitoreo simulado, Docker y AWS. No se toca el sello de la validación externa ni ningún cálculo: los números salen de `app_logica.py`, `formato.py` y los módulos existentes.
