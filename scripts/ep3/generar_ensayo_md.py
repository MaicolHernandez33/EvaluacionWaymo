"""F19-A3: genera docs/ep3/ensayo_validacion_externa.md desde data/08_reporting_ep3/ensayo_resultado.json (lo escribe ensayo_validacion_externa.py)."""
from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def c(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def mi(x):
    return f"{int(x):,}".replace(",", ".")


def main() -> None:
    r = json.loads((RAIZ / "data/08_reporting_ep3/ensayo_resultado.json").read_text(encoding="utf-8"))
    v = r["variables_vs_dev_41"]
    pasos = "\n".join(f"| {p['paso']} | `{p['comando']}` | {p['codigo']} | {c(p['segundos'])} s | {p['memoria_max_mb']} MB |" for p in r["pasos"])
    segs = "\n".join(f"| `{s['segment_id'][:12]}` | {s['estrato']} | {mi(s['asoc_filas'])} | {mi(s['lidar_filas'])} | {mi(s['positivos'])} | {c(s['tasa_etiquetado_pct'])} % | {r['segmentos'][s['segment_id'][:12]]} |" for s in r["lista"])
    det = "\n".join(f"| {d['denominador']} | {d['celdas_marcadas']} de {d['celdas_totales']} | {c(100 * d['tasa_marcadas'])} % | {c(100 * d['tasa_lo'])} % a {c(100 * d['tasa_hi'])} % |" for d in r["detector"])
    md = f"""# Ensayo general de la validación externa (con datos de DESARROLLO)

**Esto es un ensayo con datos de desarrollo, no la validación externa.** Los 4 segmentos salen de `data/01_raw/waymo` (son parte de los 41 de desarrollo), así que **sus resultados no significan nada y no se usan para decidir nada**: el objetivo es probar la tubería de punta a punta (paquete del notebook 00b, `congelar`, `ingesta_nuevos`, `evaluar --ensayo`) antes de la corrida real. *Generado por `scripts/ep3/generar_ensayo_md.py` desde `data/08_reporting_ep3/ensayo_resultado.json` (lo escribe `scripts/ep3/ensayo_validacion_externa.py`).*

## Qué se armó
En `C:/Users/maico/tmp_verificacion_ep3/ensayo_nuevos/segmentos_nuevos_ep3/` la misma estructura que produce el notebook 00b: `lidar_box/`, `camera_to_lidar_box_association/` y `segmentos_nuevos_ep3.csv` con las columnas {', '.join(f'`{x}`' for x in r['paquete_columnas'])} (las cifras se calculan con las mismas fórmulas que la celda de evaluación del notebook).

| Segmento | Estrato | Filas de asociación | Filas de lidar_box | Positivos | Tasa de etiquetado | Por qué se eligió |
|---|---|---|---|---|---|---|
{segs}

## Comandos reales (CLI) y medición
| Paso | Comando | Código de salida | Tiempo | Memoria máxima |
|---|---|---|---|---|
{pasos}

**Total: {c(r['tiempo_total_s'])} s y {r['memoria_max_mb']} MB como máximo.** Con 4 segmentos pequeños; la corrida real (hasta 26 segmentos útiles) debería ser unas decenas de segundos (extrapolación, no medida).

## Comprobaciones
1. **Variables ingeridas contra `dev_41`** (llaves: segmento, marca de tiempo, objeto): {mi(v['filas_ingeridas'])} filas ingeridas y {mi(v['filas_dev_41'])} en `dev_41`; solo en la ingesta: {v['filas_solo_en_ingesta']}; solo en `dev_41`: {v['filas_solo_en_dev_41']}; diferencia máxima en las 16 variables, `az_signed`, `c1` a `c5` y `sin_camara`: **{v['diferencia_maxima_global']:.1e}** (tolerancia {v['tolerancia']:.0e}); `en_zona_principal` igual: {'sí' if v['en_zona_principal_igual'] else 'no'}. **Coinciden: {'sí' if v['coinciden'] else 'NO'}.**
2. **El detector marca las 2 celdas de referencia:** {', '.join('`' + x + '`' for x in r['celdas_marcadas'])}. **{'Sí' if r['marca_las_2_de_referencia'] else 'NO'}**; marcadas además de esas 2: {len(r['celdas_marcadas_ademas_de_las_2'])}.
3. **Salidas:** {', '.join('`' + s + '`' for s in r['salidas_escritas'])}; faltantes: {len(r['salidas_esperadas_faltantes'])}. Incluye `externa_alternativas.csv` (las alternativas LR3 y XGBoost congeladas, DEV-4).
4. **Lo real quedó intacto:** `manifest_nuevos.json`, `nuevos.parquet` y el candado no se crearon ni modificaron: **{'sí' if r['lo_real_quedo_intacto'] else 'NO'}**.
5. **Tasa de celdas marcadas con los dos denominadores** (con 4 segmentos; en desarrollo fue 2 de 111 celdas con >= 100 cajas):

| Denominador | Marcadas | Tasa | IC 95 % por segmentos |
|---|---|---|---|
{det}

## Qué se corrigió al preparar el ensayo (antes de la corrida final, que pasó sin excepciones)
- `scripts/ep3/ingesta_nuevos.py` escribía siempre en `data/05_model_input_ep3/nuevos.parquet` (el real): un ensayo lo habría pisado. Ahora acepta `--salida` y `--resumen` y se niega a sobrescribir un `nuevos.parquet` existente (salvo `--forzar`).
- `scripts/ep3/evaluar_sellado.py` tomaba el candado antes de calcular: una falla de cálculo habría gastado el único intento. Ahora calcula todo en memoria, toma el candado justo antes de escribir y guarda en él los sha256 de las salidas; comprueba antes las entradas con mensajes claros; y el modo `--ensayo` no toma candado ni toca el manifest real (exige `--manifest`).
- El notebook 00b: el plan sellado pasó a ser obligatorio, se comprueba su hash, y se simuló todo el flujo (con un `gsutil` simulado) en `tests/ep3/test_notebook_00b_simulado.py`.
- **No apareció ninguna excepción en el recorrido de punta a punta**; lo que se arregló fueron supuestos de diseño (rutas reales, orden del candado), no errores en ejecución.

## Lo que este ensayo NO prueba
- El acceso al bucket y las descargas reales de Colab (el notebook se probó con un `gsutil` simulado).
- Cómo se comporta el detector o la regla en segmentos nuevos (los datos son de desarrollo).
- Otra máquina u otro sistema operativo.
"""
    (RAIZ / "docs/ep3/ensayo_validacion_externa.md").write_text(md, encoding="utf-8")
    print("escrito ensayo_validacion_externa.md")


if __name__ == "__main__":
    main()
