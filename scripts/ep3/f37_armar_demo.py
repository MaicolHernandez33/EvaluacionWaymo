"""F37, Pasos 1.4 y 2: arma ``datos_demo/`` a partir de los candidatos descargados y escribe ``LEEME_DEMO.md`` con las cifras MEDIDAS (nada se escribe a mano).

Entrada: ``<candidatos>/<segmento>/lidar_box.parquet`` y ``camera_to_lidar_box_association.parquet`` (lo que deja ``f37_colab_descargar.py``).
Qué hace:
  1. Mide cada candidato con el código real de la página (``inferencia.puntuar_segmento`` con la solución congelada): cajas, % sin pareja, celdas marcadas, cajas en rango por cámara.
  2. Elige: C = un candidato con celda marcada REAL si existe (el mejor ejemplo); si no, el candidato con más cajas en una cámara y se le fabrica un hueco SIMULADO (``crear_demo_hueco.py``,
     la menor fracción de {0,90; 0,95; 0,98; 1,0} que marca exactamente esa celda y solo esa). A y B = los dos candidatos sin celdas marcadas con más cajas; D = el siguiente (solo lidar_box).
  3. Copia los archivos tal cual (sin releer ni reescribir), comprueba que el lidar_box de C es idéntico byte a byte y escribe ``MANIFIESTO.json`` (sha256 y tamaño) y ``LEEME_DEMO.md``.
Se puede forzar la elección con --A --B --C --D (id de segmento). ``--tiempos`` toma los segundos de ``f37_pruebas_ui.json`` si ya se corrió ese script.
Uso: .venv\\Scripts\\python scripts/ep3/f37_armar_demo.py --candidatos datos_demo/candidatos --destino datos_demo
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RAIZ / "src"))
import f37_analizar as Z  # noqa: E402
from waymo_evaluacion.ep3.inferencia import cargar_artefactos  # noqa: E402

CAMARAS = {1: "frontal", 2: "frontal izquierda", 3: "frontal derecha", 4: "lateral izquierda", 5: "lateral derecha"}


def corto(seg: str) -> str:
    return "…" + seg[:12][-6:]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidatos", type=Path, required=True)
    ap.add_argument("--destino", type=Path, required=True)
    ap.add_argument("--A")
    ap.add_argument("--B")
    ap.add_argument("--C")
    ap.add_argument("--D")
    ap.add_argument("--tiempos", type=Path, default=None)
    a = ap.parse_args()
    art = cargar_artefactos(RAIZ / "data/06_models_ep3")
    medidas: dict[str, dict] = {}
    for carpeta in sorted(p for p in a.candidatos.iterdir() if p.is_dir()):
        lidar, asoc = Z._archivos(carpeta)
        if lidar.exists() and asoc is not None:
            medidas[carpeta.name] = Z.medir(pd.read_parquet(lidar), pd.read_parquet(asoc), art)
    if len(medidas) < 3:
        sys.exit(f"hacen falta al menos 3 candidatos con los dos archivos (hay {len(medidas)})")
    por_cajas = sorted(medidas, key=lambda s: -medidas[s]["cajas_puntuadas"])
    con_hueco_real = [s for s in por_cajas if medidas[s]["celdas_marcadas"] >= 1]
    sin_hueco = [s for s in por_cajas if medidas[s]["celdas_marcadas"] == 0]
    c_real = bool(a.C is None and con_hueco_real) or (a.C is not None and medidas[a.C]["celdas_marcadas"] >= 1)
    C = a.C or (con_hueco_real[0] if con_hueco_real else None)
    if C is None:                                                             # hueco simulado: el candidato sin celdas marcadas con más cajas en una cámara
        C = max(sin_hueco, key=lambda s: max(v["cajas_en_rango"] for v in medidas[s]["por_camara"].values()))
    resto = [s for s in sin_hueco if s != C]
    A = a.A or (resto[0] if resto else None)
    B = a.B or next((s for s in resto if s != A), None)
    D = a.D or next((s for s in por_cajas if s not in (A, B, C)), B)
    if None in (A, B):
        sys.exit("no hay dos candidatos sin celdas marcadas para A y B; use --A y --B")
    d = a.destino
    for nombre in ("A_real_sin_hueco", "B_real_sin_hueco_2", "C_hueco", "D_solo_lidar_box"):
        if (d / nombre).exists():
            sys.exit(f"{d / nombre} ya existe: no se sobrescribe (bórrela a mano si quiere rearmar)")
    origen = lambda s: Z._archivos(a.candidatos / s)                          # noqa: E731
    for nombre, seg in (("A_real_sin_hueco", A), ("B_real_sin_hueco_2", B)):
        (d / nombre).mkdir(parents=True)
        lid, aso = origen(seg)
        shutil.copyfile(lid, d / nombre / "lidar_box.parquet")
        shutil.copyfile(aso, d / nombre / "camera_to_lidar_box_association.parquet")
    (d / "D_solo_lidar_box").mkdir(parents=True)
    shutil.copyfile(origen(D)[0], d / "D_solo_lidar_box" / "lidar_box.parquet")
    lid, aso = origen(C)
    ensayo = None
    if c_real:
        (d / "C_hueco").mkdir(parents=True)
        shutil.copyfile(lid, d / "C_hueco" / "lidar_box.parquet")
        shutil.copyfile(aso, d / "C_hueco" / "camera_to_lidar_box_association.parquet")
        camara = int(str(medidas[C]["celdas"][0]["camara"])[0])
        fraccion = None
        (d / "C_hueco" / "LEEME_REAL.txt").write_text(f"Segmento REAL con una celda marcada por el detector (cámara {camara}): sin modificar.\nSegmento: {C}\n", encoding="utf-8")
    else:
        camara = max(medidas[C]["por_camara"], key=lambda c: medidas[C]["por_camara"][c]["cajas_en_rango"])
        camara = int(camara[1:])
        Z.hueco(a.candidatos / C, camara, d / "C_ensayo_fracciones.json")
        ensayo = json.loads((d / "C_ensayo_fracciones.json").read_text(encoding="utf-8"))
        fraccion = ensayo["fraccion_elegida"]
        if fraccion is None:
            sys.exit("ninguna fracción marca exactamente esa celda: elija otra cámara u otro segmento (ver C_ensayo_fracciones.json)")
        subprocess_args = ["--lidar-box", str(lid), "--asociacion", str(aso), "--camara", str(camara), "--fraccion", str(fraccion), "--semilla", str(Z.SEMILLA), "--salida", str(d / "C_hueco")]
        sys.path.insert(0, str(RAIZ / "scripts"))
        import crear_demo_hueco as crear  # noqa: E402
        if crear.main(subprocess_args) != 0:
            sys.exit("crear_demo_hueco.py falló")
        if sha(d / "C_hueco" / "lidar_box.parquet") != sha(lid):
            sys.exit("el lidar_box de C NO es idéntico al original")
    # --------------------------------------------------------------------------------------- medir lo que quedó (lo que el presentador verá)
    final = {}
    for nombre in ("A_real_sin_hueco", "B_real_sin_hueco_2", "C_hueco", "D_solo_lidar_box"):
        lidar_p, asoc_p = Z._archivos(d / nombre)
        final[nombre] = Z.medir(pd.read_parquet(lidar_p), pd.read_parquet(asoc_p) if asoc_p else None, art)
    manifiesto = {"origen": {"A": A, "B": B, "C": C, "D": D}, "C_es_real": c_real, "C_camara": camara, "C_fraccion": fraccion, "medidas_candidatos": medidas, "medidas_finales": final,
                  "archivos": {str(p.relative_to(d)).replace("\\", "/"): {"bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(d.rglob("*.parquet"))},
                  "tamano_mb": {n: round(sum(p.stat().st_size for p in (d / n).rglob("*") if p.is_file()) / 1024 / 1024, 2) for n in final}}
    (d / "MANIFIESTO.json").write_text(json.dumps(manifiesto, indent=1, ensure_ascii=False), encoding="utf-8")
    tiempos = json.loads(a.tiempos.read_text(encoding="utf-8"))["pruebas"] if a.tiempos and a.tiempos.exists() else None
    (d / "LEEME_DEMO.md").write_text(guion(manifiesto, tiempos), encoding="utf-8")
    print(json.dumps({k: manifiesto[k] for k in ("origen", "C_es_real", "C_camara", "C_fraccion", "tamano_mb")}, ensure_ascii=False))


def n(x: int) -> str:
    return f"{x:,}".replace(",", ".")


def guion(m: dict, tiempos: dict | None) -> str:
    fa, fc, fd = m["medidas_finales"]["A_real_sin_hueco"], m["medidas_finales"]["C_hueco"], m["medidas_finales"]["D_solo_lidar_box"]
    cam = m["C_camara"]
    celda = fc["celdas"][0]
    seg = {k: corto(v) for k, v in m["origen"].items()}
    t = ""
    if tiempos:
        t = (f"\nTiempos medidos en la interfaz (3 repeticiones): A, mediana {tiempos['A_completo']['mediana']:.1f} s y peor {tiempos['A_completo']['peor']:.1f} s; "
             f"C, mediana {tiempos['C_completo']['mediana']:.1f} s y peor {tiempos['C_completo']['peor']:.1f} s.\n")
    como = (f"Es un segmento real que ya traía una celda marcada por el detector (cámara {cam}); no se modificó." if m["C_es_real"] else
            f"**Es una falla de cámara SIMULADA sobre un segmento real.** Se borró al azar el {int(round(100 * m['C_fraccion']))} % de las asociaciones de la cámara {cam} ({CAMARAS[cam]}) con "
            f"`scripts/crear_demo_hueco.py` (semilla {Z.SEMILLA}); el archivo lidar_box es el original, idéntico byte a byte.")
    frase = ("«Este segmento ya traía un posible hueco de cámara; el detector lo marcó solo.»" if m["C_es_real"] else
             "«Este archivo lo modifiqué a propósito: tomé un segmento real y le borré las parejas 2D de una cámara para simular una falla. Quiero ver si la página la detecta. "
             "No es un hallazgo del dataset.»")
    return f"""# Demostración en vivo: «Puntuar datos nuevos» (F37)

*Cifras medidas con el código real de la página y la solución congelada; se regeneran con `scripts/ep3/f37_armar_demo.py`. Estos segmentos NO son de los 41 de desarrollo ni de los candidatos del plan sellado.*

## Qué hay en esta carpeta
| Carpeta | Qué es | Segmento |
|---|---|---|
| `A_real_sin_hueco/` | segmento real nuevo, sin tocar, sin celdas marcadas | {seg['A']} |
| `B_real_sin_hueco_2/` | segundo segmento real nuevo, sin tocar (respaldo) | {seg['B']} |
| `C_hueco/` | {'segmento real con una celda marcada' if m['C_es_real'] else 'segmento real con falla de cámara SIMULADA (el archivo 2 dice SIMULADO en el nombre)'} | {seg['C']} |
| `D_solo_lidar_box/` | solo `lidar_box.parquet` (para mostrar qué pasa sin el archivo 2) | {seg['D']} |

## Antes de empezar (1 minuto)
1. Abra la página, menú **Herramientas › Puntuar datos nuevos**. Tenga las carpetas abiertas en el explorador, una al lado de la otra.
2. **Los dos archivos se pueden subir en cualquier orden.** Nada se puntúa al subir: se puntúa al pulsar «Puntuar segmento» (desde F39; antes había que subir primero el archivo 2).
3. Cada archivo pesa menos de 3 MB; el puntaje tarda alrededor de 1 segundo.{t}
## Guion (unos 90 segundos)
**Paso 1 · Caso normal (A).** Suba `A_real_sin_hueco/camera_to_lidar_box_association.parquet` y luego `A_real_sin_hueco/lidar_box.parquet`.
Debe verse: «Segmento {seg['A']}», **Celdas marcadas 0 de 5**, {n(fa['cajas_puntuadas'])} cajas puntuadas, {n(fa['cajas_en_cola'])} cajas en la cola y {str(fa.get('pct_sin_pareja')).replace('.', ',')} % de cajas sin pareja 2D.
Decir: «Un segmento real que la solución nunca vio. Sin huecos de cámara: todas las cajas quedan en la cola, de más a menos probable de no tener pareja.»

**Paso 2 · Caso con hueco (C).** Pulse «Cargar otro segmento». Suba `C_hueco/{'camera_to_lidar_box_association' + ('__SIMULADO_hueco_cam' + str(cam) if not m['C_es_real'] else '')}.parquet` y luego `C_hueco/lidar_box.parquet`.
Debe verse: «Segmento {seg['C']}», **Celdas marcadas 1 de 5** (cámara {cam}, {CAMARAS[cam]}), {n(fc['cajas_en_celdas_marcadas'])} cajas afectadas, {n(fc.get('sin_pareja', 0))} cajas sin pareja en total ({str(fc.get('pct_sin_pareja')).replace('.', ',')} %), y la cola con {n(fc['cajas_en_cola'])} cajas (las de la celda marcada salen de la cola y se auditan aparte).
Tasa de pares de esa celda: {str(round(100 * celda['tasa'], 1)).replace('.', ',')} %, bajo el umbral de hueco de {str(round(100 * celda['umbral'], 1)).replace('.', ',')} % (25 % de la tasa normal de la cámara; mínimo 100 cajas en el rango). {como}
Decir: {frase}

**Paso 3 · Resumen.** Vaya a «Resumen» (barra lateral). Las cifras de arriba no cambian (siguen siendo los 41 segmentos de desarrollo); abajo aparece **«Segmentos puntuados en esta sesión»** con las dos filas y la línea «No forman parte de las cifras congeladas».

**Paso 4 (opcional, 15 s) · Sin archivo 2 (D).** «Cargar otro segmento»; suba solo `D_solo_lidar_box/lidar_box.parquet`. Debe verse: Celdas marcadas «—», {n(fd['cajas_puntuadas'])} cajas puntuadas y el aviso «No se buscaron huecos de cámara: falta el archivo 2».

## Qué NO decir
- Que el segmento C es un hallazgo real, si es simulado.
- Que estos resultados validan la solución: es una prueba de funcionamiento; la validación con segmentos nuevos sigue sellada y sin ejecutar.

## Plan B (si algo falla en vivo)
1. Pulse «Cargar otro segmento» (o recargue la página con F5).
2. Use el botón **«Usar un segmento de desarrollo de ejemplo»**: puntúa un segmento de desarrollo (…534050) y muestra su celda marcada real (**1 de 5**, cámara 5, 268 cajas afectadas y 227 sin pareja) y su cola. Dígalo: es de desarrollo, no nuevo, y sus celdas ya estaban calculadas con su archivo de asociación (no se reconstruyen).
3. Si el archivo no sube, pruebe con `B_real_sin_hueco_2/` (mismo procedimiento que A).
"""


if __name__ == "__main__":
    main()
