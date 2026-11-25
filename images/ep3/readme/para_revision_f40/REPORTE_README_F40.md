# REPORTE F40: README final (2026-11-24)

Escrito para: quien revisa el README antes de la presentación. El README se regeneró con `scripts/generar_readme.py` (nunca a mano). **No hay commit** (instrucción del proyecto).

## Qué cambió en el README (797 líneas, tope 800)
| Pedido | Hecho |
|---|---|
| 1. Prueba con segmentos nuevos | Subsección «Prueba con segmentos nuevos» en la sección 16, con una tabla de los 4 segmentos y su celda marcada (cámara 5: 225 cajas en el rango, 197 afectadas, 175 sin pareja, tasa de pares 0,0 % frente a 91,4 % de referencia). Sale de `docs/ep3/prueba_segmentos_nuevos.json` (lo genera `scripts/ep3/f40_prueba_segmentos_nuevos.py` con las mismas funciones de la página; incluye el sha256 de cada archivo). Dice «prueba de funcionamiento, no una validación estadística». Actualizados: «Límites» de «En breve», nota de alcance de la sección 1, viñeta de 8.3, «Lo que NO afirmamos» (sección 12) y «Prueba en vivo» (flujo de F39: dos archivos en cualquier orden y «Puntuar segmento»). |
| 2. Recuadro de 8.1 | Recuadro bajo el título de 8.1 y tabla de dos filas «EP2 frente a EP3» con los AUC calculados de `cajas_oof.parquet` (regla: 0,862 en los 33 de entrenamiento, 0,684 en los 8 de test, 0,823 en los 41). Referencias desde 8.3 y desde los KPI de la sección 2. Se corrigió 8.3, que decía `GroupKFold` de 5: es `StratifiedGroupKFold` de 5 estratificado por `sin_camara`. |
| 3. Sección 17 | Sin «Pendiente»; frase neutra; fila con las opciones del docente (`opciones_docente` en `docs/ep3/readme_entradas.json`); fila de la validación nueva. |
| 4. Estructura | Árbol de la raíz generado del sistema de archivos y tabla de los 19 notebooks (número, nombre, etapa, propósito, orden y qué consta sobre su ejecución, con las celdas con salida contadas del `.ipynb`). Si falta una descripción, el generador falla. |
| 5. Pruebas | Remedidas: EP3 415 de 415 (2026-11-24 20:38) y EP2 81 de 81 en copia temporal. |
| 6. Controles | Sin «Pendiente», «TODO», «xxx», `<` ni «borrador» (salvo el aviso del modo publicado y el estado «en preparación»); enlaces, anclas, imágenes y `<details>` verificados por `tests/ep3/test_readme_f38.py`; 4 capturas de `images/app/` rehechas con la interfaz de F39. |

## Cifras README frente al Resumen
Las 6 cifras coinciden con las que calcula la página (ver `diff_resumen.txt`): 80.571 cajas, 205 celdas, 2 marcadas, 1.945 afectadas, 78.626 en la cola, 41 segmentos. No se perdió ninguna cifra: las pruebas anteriores del README siguen pasando.

## Pruebas
- Suite completa en copia temporal: **496 passed** (antes 488; +8 de F40). `tests/ep3` real: 415 de 415. Congelados: 14 de 14 y 5 de 5. Sello intacto (`sello_despues.json`).
- Pruebas nuevas (8 en `tests/ep3/test_readme_f38.py`): tope de líneas y marcadores, prueba de segmentos nuevos frente al JSON, sha256 de entradas, AUC del recuadro recalculados, tabla de notebooks, árbol, sección 17 y remediciones. Se ajustaron dos antiguas que exigían el texto «Pendiente».
- La prueba del README del conteo de pruebas (el fallo conocido de F41) quedó resuelta al regenerar.

## Cosas a saber
- **Tope de 800 líneas:** para entrar hubo que poner cada imagen junto a su pie y unir algunos párrafos consecutivos con negrita (también en secciones de EP2: solo cambia el espacio entre párrafos, no el texto). Queda un margen de 3 líneas: cualquier agregado exige recortar.
- **Cobertura de EP2:** no se publica una cifra nueva. En la copia temporal el paquete se importa del repositorio real, y la cobertura medida (46,5 %) no es la de EP2 (92,7 %, medida en EP2). Se dice en el README.
- **Retroalimentación de EP1 y EP2:** sigue vacía; el README ya no dice «Pendiente» y no inventa nada. Si el equipo la tiene, va en `docs/ep3/readme_entradas.json` y se regenera.
- **URL de despliegue:** vacía; el README dice «en preparación».
- Las capturas del README son de `images/app/` (la página real). Las 3 de esta carpeta usan un conversor mínimo de Markdown, no el render exacto de GitHub.
- Los commits de F41 y F40 siguen sin hacerse.

## Archivos de esta carpeta (9)
`README.md`, `REPORTE_README_F40.md`, `diff_resumen.txt`, `resultado_pytest.txt`, `estado_git.txt`, `sello_despues.json`, y 3 capturas (`readme_01_parte_superior.png`, `readme_02_seccion_8_1_con_recuadro.png`, `readme_03_prueba_con_segmentos_nuevos.png`).
