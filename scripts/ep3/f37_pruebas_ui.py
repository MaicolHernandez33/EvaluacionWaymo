"""F37, Paso 3: pruebas de extremo a extremo EN LA INTERFAZ de «Puntuar datos nuevos» (y del bloque del Resumen), con el uploader real (``DOM.setFileInputFiles``) y un navegador sin interfaz.

Es lo que haría el presentador: sube archivos, mide los segundos hasta ver el resultado, cambia de segmento sin recargar y revisa que no queden resultados ni errores viejos. Con la página corriendo en localhost.
``--datos`` es la carpeta con ``A_real_sin_hueco``, ``B_real_sin_hueco_2``, ``C_hueco`` y ``D_solo_lidar_box`` (cada una con ``lidar_box.parquet`` y, salvo D, su archivo de asociación). Sirve igual con
el ensayo (segmentos de desarrollo, que no valen como demo) y con ``datos_demo`` real: el JSON dice qué carpeta se usó. Escribe ``--salida`` (JSON) y las capturas en ``--capturas`` (1366 px).
OBSOLETO desde F39 (el puntaje ya no se dispara al subir el archivo 1: usar ``f39_pruebas_ui.py``). Lo que sigue describe el flujo de F37.
IMPORTANTE para el presentador (flujo de F37): con los dos uploaders, el archivo 1 dispara el puntaje apenas termina de subir; por eso el orden es ARCHIVO 2 primero y ARCHIVO 1 después (el script lo hace así y mide qué pasa al revés).
Uso: .venv\\Scripts\\python scripts/ep3/f37_pruebas_ui.py --puerto 8531 --datos datos_demo --salida docs/ep3/f37_pruebas_ui.json --capturas images/ep3/pagina/para_revision_f37
"""
from __future__ import annotations

import argparse
import base64
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RAIZ / "src"))
import capturar_pagina as C  # noqa: E402
import f31_f33_capturas as F  # noqa: E402

CLAVE_P = C.CLAVE["Puntuar datos nuevos"]
JS_ESTADO = """(() => {
  const res = document.querySelector('[class*=st-key-pt_resultado]');
  const avisos = Array.from(document.querySelectorAll('.aud-aviso')).map(e => e.innerText.trim());
  const sub = document.querySelectorAll('[class*=st-key-rs_sesion]');
  const subidores = document.querySelectorAll('[data-testid=stFileUploader]').length;
  const archivos = Array.from(document.querySelectorAll('[data-testid=stFileUploaderFile]')).map(e => e.innerText.split('\\n')[0].trim());
  const celdas = document.querySelector('[class*=st-key-pt_celdas]');
  return JSON.stringify({resultado: !!res, texto: res ? res.innerText : '', avisos: avisos, spinner: !!document.querySelector('[data-testid=stSpinner]'), bloque_sesion: sub.length ? sub[0].innerText : '',
                         subidores: subidores, archivos: archivos, celdas: celdas ? celdas.innerText : '', excepcion: !!document.querySelector('[data-testid=stException]')});
})()"""
JS_MAIN = "(() => document.querySelector('[data-testid=\"stMainBlockContainer\"]').innerText)()"


def archivos(carpeta: Path) -> tuple[Path, Path | None]:
    lidar = carpeta / "lidar_box.parquet"
    asoc = sorted(carpeta.glob("camera_to_lidar_box_association*.parquet"))
    return lidar, (asoc[0] if asoc else None)


def estado(nav: C.Navegador) -> dict:
    return nav.js(JS_ESTADO) or {}


def subir(nav: C.Navegador, indice: int, ruta: Path) -> None:
    doc = nav.cmd("DOM.getDocument", depth=-1)
    ids = nav.cmd("DOM.querySelectorAll", nodeId=doc["root"]["nodeId"], selector="input[type=file]")["nodeIds"]
    nav.cmd("DOM.setFileInputFiles", files=[str(ruta)], nodeId=ids[indice])


def esperar(nav: C.Navegador, maximo: float = 90.0, hasta: str = "resultado_o_aviso") -> tuple[dict, float]:
    """Espera (cada 0,1 s) a que aparezca el resultado o un aviso y no haya spinner; devuelve el estado y los segundos."""
    t0 = time.time()
    ultimo: dict = {}
    while time.time() - t0 < maximo:
        ultimo = estado(nav)
        if not ultimo.get("spinner") and (ultimo.get("resultado") or ultimo.get("avisos")):
            time.sleep(0.4)                                       # un último vistazo: que no cambie justo después
            ultimo = estado(nav)
            return ultimo, time.time() - t0
        time.sleep(0.1)
    return ultimo, time.time() - t0


def abrir(nav: C.Navegador, puerto: int, seccion: str) -> None:
    F.abrir(nav, puerto, seccion, C.CLAVE[seccion])


def ir_por_menu(nav: C.Navegador, puerto: int, texto: str, clave: dict) -> None:
    """Cambia de página con el enlace de la barra lateral (sin recargar: la sesión sigue)."""
    ok = nav.js("(() => { const a = Array.from(document.querySelectorAll('a')).find(x => x.href === %s); if (!a) return false; a.click(); return true; })()" % json.dumps(C.url(puerto, texto)))
    if not ok:
        raise RuntimeError(f"no encontré el enlace de la barra lateral para {texto}")
    time.sleep(2.5)
    F.estable(nav, texto, clave, 1.5)


def cargar_completo(nav: C.Navegador, lidar: Path, asoc: Path | None) -> tuple[dict, float]:
    """Sube primero el archivo 2 y después el 1 (como se debe en vivo); mide desde que se sube el archivo 1."""
    if asoc is not None:
        subir(nav, 1, asoc)
        time.sleep(2.5)
    t0 = time.time()
    subir(nav, 0, lidar)
    est, _ = esperar(nav)
    return est, time.time() - t0


def otro_segmento(nav: C.Navegador) -> None:
    nav.js(f"({F.JS_CLIC_TEXTO})('button', 'Cargar otro segmento', true)")
    time.sleep(2.0)
    F.estable(nav, "Puntuar datos nuevos", CLAVE_P, 1.0)


def resumen_corto(est: dict) -> dict:
    lineas = [x.strip() for x in est.get("texto", "").split("\n") if x.strip()]
    return {"resultado": est.get("resultado"), "avisos": est.get("avisos"), "lineas": lineas[:16], "excepcion": est.get("excepcion")}


def foto(nav: C.Navegador, destino: Path, nombre: str, alto_max: int = 1500, y0: float = 0, alto: float | None = None) -> dict:
    al = float(nav.js("Math.ceil(document.querySelector('[data-testid=\"stMainBlockContainer\"]').getBoundingClientRect().bottom)")) + 30 if alto is None else alto
    nav.cmd("Emulation.setDeviceMetricsOverride", width=F.ANCHO, height=int(min(max(al, 700), 3600)), deviceScaleFactor=1, mobile=False)
    time.sleep(0.8)
    nav.js("(() => { window.scrollTo(0, 0); return true; })()")
    datos = nav.cmd("Page.captureScreenshot", format="png", clip={"x": 0, "y": y0, "width": F.ANCHO, "height": int(min(al - y0, alto_max)), "scale": 1})["data"]
    destino.mkdir(parents=True, exist_ok=True)
    (destino / f"{nombre}.png").write_bytes(base64.b64decode(datos))
    print(f"OK   {nombre} {F.ANCHO} x {int(min(al - y0, alto_max))}")
    return {"archivo": f"{nombre}.png", "ancho": F.ANCHO, "alto": int(min(al - y0, alto_max))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8531)
    ap.add_argument("--debug", type=int, default=9381)
    ap.add_argument("--datos", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    ap.add_argument("--capturas", type=Path, required=True)
    ap.add_argument("--repeticiones", type=int, default=3)
    a = ap.parse_args()
    A, B, Cc, D = (archivos(next(a.datos.glob(p))) for p in ("A_*", "B_*", "C_*", "D_*"))
    out: dict = {"datos": str(a.datos), "carpetas": {k: next(a.datos.glob(k + "_*")).name for k in "ABCD"}, "pruebas": {}}
    caps: list[dict] = []
    nav = C.Navegador(a.debug)
    try:
        # ---------------------------------------------------------------------------------------- 1 y 2: A y C completos, con tiempos
        for nombre, (lid, aso) in (("A", A), ("C", Cc)):
            tiempos, detalle = [], None
            for i in range(a.repeticiones):
                abrir(nav, a.puerto, "Puntuar datos nuevos")
                est, seg = cargar_completo(nav, lid, aso)
                tiempos.append(round(seg, 2))
                detalle = resumen_corto(est)
                if i == 0:
                    caps.append(foto(nav, a.capturas, "f37_01_A_cargado" if nombre == "A" else "f37_02_C_cargado_con_celda_marcada"))
            out["pruebas"][f"{nombre}_completo"] = {"segundos": tiempos, "mediana": statistics.median(tiempos), "peor": max(tiempos), "resultado": detalle}
            print(nombre, tiempos, detalle["lineas"][:8] if detalle else None)
        # ---------------------------------------------------------------------------------------- 3: D solo con archivo 1
        abrir(nav, a.puerto, "Puntuar datos nuevos")
        t0 = time.time()
        subir(nav, 0, D[0])
        est, _ = esperar(nav)
        out["pruebas"]["D_solo_archivo_1"] = {"segundos": round(time.time() - t0, 2), "resultado": resumen_corto(est), "celdas": est.get("celdas")}
        caps.append(foto(nav, a.capturas, "f37_03_D_solo_archivo_1"))
        # ---------------------------------------------------------------------------------------- 4: cambios de estado en una sola sesión (sin recargar)
        trans: dict = {}
        abrir(nav, a.puerto, "Resumen")
        trans["resumen_antes"] = nav.js(JS_MAIN)
        trans["resumen_antes_bloque"] = estado(nav)["bloque_sesion"]
        ir_por_menu(nav, a.puerto, "Puntuar datos nuevos", CLAVE_P)
        est, _ = cargar_completo(nav, *A)
        trans["A"] = resumen_corto(est)
        otro_segmento(nav)
        est, _ = cargar_completo(nav, *Cc)
        trans["A_a_C"] = resumen_corto(est)
        otro_segmento(nav)
        est, _ = cargar_completo(nav, *A)
        trans["C_a_A"] = resumen_corto(est)
        otro_segmento(nav)
        # volver a subir el mismo archivo (A otra vez)
        est, _ = cargar_completo(nav, *A)
        trans["mismo_archivo_otra_vez"] = resumen_corto(est)
        otro_segmento(nav)
        # quitar el archivo 2 después de cargarlo y antes del archivo 1
        subir(nav, 1, Cc[1])
        time.sleep(2.5)
        nav.js("(() => { const b = document.querySelector('[data-testid=stFileUploaderDeleteBtn] button'); if (b) b.click(); return !!b; })()")
        time.sleep(2.0)
        trans["quitar_archivo_2_estado"] = {"archivos_visibles": estado(nav)["archivos"]}
        subir(nav, 0, Cc[0])
        est, _ = esperar(nav)
        trans["quitar_archivo_2_y_subir_1"] = resumen_corto(est)
        otro_segmento(nav)
        # subir el archivo 1 primero (el orden «equivocado»): puntúa de inmediato sin archivo 2
        subir(nav, 0, Cc[0])
        est, _ = esperar(nav)
        trans["archivo_1_primero"] = resumen_corto(est) | {"subidores_despues": est.get("subidores")}
        otro_segmento(nav)
        # el 2 de un segmento con el 1 de OTRO
        subir(nav, 1, B[1])
        time.sleep(2.5)
        subir(nav, 0, A[0])
        est, _ = esperar(nav)
        trans["archivo_2_de_otro_segmento"] = resumen_corto(est)
        caps.append(foto(nav, a.capturas, "f37_05_error_segmentos_distintos"))
        # un error y enseguida un segmento bueno: no debe quedar el aviso viejo
        subir(nav, 1, A[1])
        time.sleep(2.5)
        est, _ = esperar(nav)
        trans["corregir_el_archivo_2"] = resumen_corto(est)
        # archivo que no es parquet
        abrir(nav, a.puerto, "Puntuar datos nuevos")
        with tempfile.TemporaryDirectory(prefix="f37_malo_") as tmp:
            malo = Path(tmp) / "no_es_parquet.parquet"
            malo.write_text("esto no es un parquet", encoding="utf-8")
            subir(nav, 0, malo)
            est, _ = esperar(nav)
            trans["no_es_parquet"] = resumen_corto(est)
            caps.append(foto(nav, a.capturas, "f37_04_error_archivo_invalido"))
        out["pruebas"]["transiciones"] = trans
        # ---------------------------------------------------------------------------------------- 6: botón de ejemplo
        abrir(nav, a.puerto, "Puntuar datos nuevos")
        nav.js(f"({F.JS_CLIC_TEXTO})('button', 'Usar un segmento de desarrollo de ejemplo', true)")
        est, seg = esperar(nav)
        out["pruebas"]["ejemplo"] = {"segundos": round(seg, 2), "resultado": resumen_corto(est)}
        # ---------------------------------------------------------------------------------------- Resumen antes y después (una sola sesión, dos segmentos puntuados)
        abrir(nav, a.puerto, "Resumen")
        antes = nav.js(JS_MAIN)
        caps.append(foto(nav, a.capturas, "f37_06_resumen_antes"))
        ir_por_menu(nav, a.puerto, "Puntuar datos nuevos", CLAVE_P)
        cargar_completo(nav, *A)
        otro_segmento(nav)
        cargar_completo(nav, *Cc)
        ir_por_menu(nav, a.puerto, "Resumen", C.CLAVE["Resumen"])
        despues = nav.js(JS_MAIN)
        bloque = estado(nav)["bloque_sesion"]
        caps.append(foto(nav, a.capturas, "f37_07_resumen_despues"))
        la, ld = antes.splitlines(), despues.splitlines()
        out["pruebas"]["resumen"] = {"antes_sin_bloque": estado_vacio(antes), "bloque": bloque, "todo_lo_anterior_sigue": all(x in set(ld) for x in la),
                                     "lineas_nuevas": [x for x in ld if x not in set(la)][:30], "lineas_que_faltan": [x for x in la if x not in set(ld)][:30]}
        # tamaños de archivo subidos
        out["tamano_mb"] = {k: round(sum(p.stat().st_size for p in v if p) / 1024 / 1024, 2) for k, v in (("A", A), ("C", Cc), ("D", D), ("B", B))}
    finally:
        nav.cerrar()
    a.salida.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    (a.capturas / "capturas.json").write_text(json.dumps(caps, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"escrito {a.salida}")


def estado_vacio(texto: str) -> bool:
    return "Segmentos puntuados en esta sesión" not in texto


if __name__ == "__main__":
    main()
