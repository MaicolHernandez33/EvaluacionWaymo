# Guía de estilo de la página

*Generada por `scripts/ep3/generar_guia_estilo.py` desde `app/estilos.py` y `src/waymo_evaluacion/ep3/app_logica.py`. La prueba `tests/ep3/test_pagina_rediseno.py` exige el contraste y que el tema de Streamlit use estos tokens.*

## Producto
- **Nombre:** Auditor de etiquetas 3D (neutro: no usa la marca ni el logo de Waymo; la fuente de datos solo se cita en el pie: «Waymo Open Dataset v2, uso académico»).
- **Eslogan:** Revise primero las cajas que más probablemente no tienen su par en cámara.
- **Ícono:** `app/assets/icono.png`, dibujado por `scripts/ep3/generar_icono_pagina.py` (una caja 3D con una marca de verificación: una persona revisa).
- **Secciones (8):** Inicio, Auditoría de cámaras, Cola de revisión, Explica una caja, Evidencia, Ética y límites, Puntuar datos nuevos, Ayuda y glosario.

## Paleta (tokens)
Azul profundo como color primario, un acento verde azulado, ámbar para avisos, rojo para huecos y grises neutros. Apta para daltonismo: el rojo de los huecos nunca va solo (siempre con contorno grueso y una «X» en el mapa, y con texto), y las celdas sanas usan una escala de un solo tono (azul).

| Token | Valor | Uso |
|---|---|---|
| `primario` | `#1D4E89` | títulos, botón principal, enlaces, celdas sanas del mapa |
| `primario_oscuro` | `#14365F` | texto sobre fondos de énfasis |
| `acento` | `#0B6E69` | datos positivos y pasos |
| `texto` | `#1B2430` | texto principal |
| `texto_suave` | `#4A5568` | texto secundario y notas |
| `fondo` | `#FFFFFF` | fondo de la página |
| `superficie` | `#F2F5F9` | tarjetas y barra lateral |
| `borde` | `#D5DCE6` | bordes y separadores (decorativo) |
| `aviso_fondo` | `#FFF4D6` | fondo de los avisos «en muestra» y de las advertencias |
| `aviso_texto` | `#5C3D00` | texto de los avisos |
| `aviso_borde` | `#C98A00` | borde de avisos (decorativo) |
| `hueco` | `#B42318` | huecos de cámara (rojo) |
| `hueco_fondo` | `#FDECEA` | fondo de las insignias de hueco |

## Contraste (WCAG, mínimo 4,5:1 en texto)
| Par | Razón | Estado |
|---|---|---|
| texto sobre fondo | 15.65:1 | cumple |
| texto sobre superficie | 14.31:1 | cumple |
| texto_suave sobre fondo | 7.53:1 | cumple |
| texto_suave sobre superficie | 6.88:1 | cumple |
| primario sobre fondo | 8.39:1 | cumple |
| primario sobre superficie | 7.67:1 | cumple |
| fondo sobre primario | 8.39:1 | cumple |
| fondo sobre primario_oscuro | 12.19:1 | cumple |
| acento sobre fondo | 6.09:1 | cumple |
| acento sobre superficie | 5.57:1 | cumple |
| aviso_texto sobre aviso_fondo | 9.03:1 | cumple |
| hueco sobre fondo | 6.57:1 | cumple |
| hueco sobre hueco_fondo | 5.75:1 | cumple |

## Tipografía y espaciado
- Tipografía del sistema (`font = "sans serif"`; la fuente que incluye Streamlit en su paquete). **Sin fuentes externas, sin CDN, sin imágenes remotas:** una prueba falla si algún archivo de `app/` contiene `http://` o `https://`.
- Escala: cuerpo 1 rem; títulos de tarjeta 0,92 rem; cifras de tarjeta 2 rem; modo presentación multiplica por 1,18.
- Espaciado: xs = 0.25rem, s = 0.5rem, m = 1rem, l = 1.5rem, xl = 2rem (se aplican como márgenes y separaciones de las tarjetas y bloques).

## Componentes
- **Tarjeta de cifra** (`aud-tarjeta`): título, cifra grande, nota. Borde superior de color: azul (neutro), verde azulado, ámbar (estimaciones) o rojo (huecos).
- **Insignia** (`aud-insignia`): perfil activo, avisos.
- **Aviso «en muestra»**: compacto, siempre visible (no en un tooltip), con un expander «¿Qué significa?» con el texto completo.
- **Pasos** (`aud-paso`): «Cómo funciona» en 3 pasos dibujados con HTML y CSS propios.
- **Resultado destacado** (`aud-resultado`): la frase principal de la cola.
- **Pie**: versión de la solución, fuente de datos, «Una persona revisa y decide», «Nada se guarda ni se envía».

## Íconos
Material Icons de Streamlit (`:material/nombre:`), sin emojis (una prueba lo vigila).

| Sección | Ícono |
|---|---|
| Inicio | `material/home` |
| Auditoría de cámaras | `material/videocam` |
| Cola de revisión | `material/format_list_numbered` |
| Explica una caja | `material/help` |
| Evidencia | `material/science` |
| Ética y límites | `material/balance` |
| Puntuar datos nuevos | `material/upload_file` |
| Ayuda y glosario | `material/menu_book` |

## Números y redacción
- **Formato es-CL** (`src/waymo_evaluacion/ep3/formato.py`, con pruebas): miles con punto (80.571), decimales con coma (87,4), porcentaje con espacio (70,3 %).
- **Sin jerga** ni nombres de columna en snake_case en pantalla: las tablas pasan por `tabla_legible`. Se evita «recall» como titular: se dice «unas 70 de cada 100 cajas sin pareja».
- **Términos definidos** en «Ayuda y glosario»: caja, par 2D, celda, hueco, cola, presupuesto, cobertura, intervalo de confianza, post hoc, en muestra, sin prueba ciega.
- Las celdas que marca el detector se llaman **celdas marcadas** (DEV-3), nunca «falsas alarmas».
- Toda cifra del flujo en dos pasos lleva el aviso «en muestra».
