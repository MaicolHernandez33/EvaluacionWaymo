"""F39: pruebas de estado de «Puntuar datos nuevos» en el navegador real (Chrome sin interfaz) con los cargadores reales (``DOM.setFileInputFiles``), sin atajos de código, y las capturas de revisión.

Recorre en UNA sola sesión (sin recargar) los casos del prompt: 1 luego 2 luego Puntuar; 2 luego 1 luego Puntuar; solo 1; solo 1 y después agregar el 2; quitar el 2 tras puntuar; cambiar el 1 por otro segmento tras
puntuar; archivo 2 de otro segmento; archivo que no es parquet; «Cargar otro segmento» y repetir; el botón de ejemplo. En cada caso comprueba que lo que hay en pantalla corresponde a los archivos actuales (sin
cifras ni errores de un intento anterior) y que las cifras son las de la línea base (``f39_regresion_antes.json``). Con la página corriendo en localhost.
Uso: .venv\\Scripts\\python scripts/ep3/f39_pruebas_ui.py --puerto 8531 --salida docs/ep3/f39_pruebas_ui.json --capturas images/ep3/pagina/para_revision_f39
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RAIZ / "src"))
import capturar_pagina as C  # noqa: E402
import f31_f33_capturas as F  # noqa: E402
from f37_pruebas_ui import subir  # noqa: E402

BASE = RAIZ / "datos_demo/candidatos"
HUECO = "16229547658178627464_380_000_400_000"          # 1 celda marcada (cámara 5)
CERO = "10689101165701914459_2072_300_2092_300"           # 0 celdas marcadas
GRANDE = "13356997604177841771_3360_000_3380_000"         # el de más cajas (7.854)
AYUDA_1 = "Todavía no agregó el archivo 2: se puntuará sin buscar huecos de cámara."
AYUDA_2 = "Listo para puntuar con búsqueda de huecos de cámara."
CAMBIARON = "Cambiaron los archivos: pulse Puntuar segmento para actualizar el resultado."

JS_ESTADO = """(() => {
  const res = document.querySelector('[class*=st-key-pt_resultado]');
  const avisos = Array.from(document.querySelectorAll('.aud-aviso')).map(e => e.innerText.trim());
  const bot = Array.from(document.querySelectorAll('button')).filter(b => b.textContent.trim() === 'Puntuar segmento');
  const arch = Array.from(document.querySelectorAll('[data-testid=stFileChip]')).map(e => (e.getAttribute('aria-label') || '').split(', ')[0]);
  const ay = document.querySelector('.aud-ayuda-flujo'); const pasos = document.querySelector('.aud-flujo');
  const exp = Array.from(document.querySelectorAll('details')).find(d => d.querySelector('summary') && d.querySelector('summary').textContent.includes('Archivos del segmento'));
  const ses = document.querySelector('[class*=st-key-rs_sesion]');
  return JSON.stringify({resultado: !!res, texto: res ? res.innerText : '', avisos: avisos, boton: bot.length ? {habilitado: !bot[0].disabled} : null, archivos: arch, ayuda: ay ? ay.innerText.trim() : '',
    pasos: pasos ? pasos.innerText : '', expander: exp ? {abierto: exp.open} : null, vacio: document.body.innerText.includes('Todavía no hay un segmento cargado'),
    titulo: res && res.querySelector('.aud-seg-t') ? res.querySelector('.aud-seg-t').innerText : '', lineas_seg: res ? Array.from(res.querySelectorAll('.aud-seg-a')).map(e => e.innerText) : [],
    spinner: !!document.querySelector('[data-testid=stSpinner]'), excepcion: !!document.querySelector('[data-testid=stException]'), sesion: ses ? ses.innerText : ''});
})()"""


def est(nav) -> dict:
    return nav.js(JS_ESTADO) or {}


def espera(nav, cond, maximo: float = 60.0, pausa: float = 0.5) -> dict:
    """Espera (cada 0,2 s) a que se cumpla ``cond`` sin spinner y con la página quieta un instante."""
    t0 = time.time()
    e: dict = {}
    while time.time() - t0 < maximo:
        e = est(nav)
        if not e.get("spinner") and cond(e):
            time.sleep(pausa)
            e = est(nav)
            if cond(e):
                return e
        time.sleep(0.2)
    return e


def clic(nav, texto: str) -> bool:
    return bool(nav.js("(() => { const b = Array.from(document.querySelectorAll('button')).find(x => x.textContent.trim() === %s && !x.disabled); if (!b) return false; b.click(); return true; })()" % json.dumps(texto)))


def abrir_exp(nav) -> None:
    """Abre el bloque plegable «Archivos del segmento» si está cerrado (cerrado, la lista de archivos y sus «x» no se dibujan)."""
    nav.js("(() => { const d = Array.from(document.querySelectorAll('details')).find(x => x.querySelector('summary') && x.querySelector('summary').textContent.includes('Archivos del segmento')); if (d && !d.open) d.querySelector('summary').click(); return !!d; })()")
    time.sleep(1.0)


def quitar(nav, cargador: str) -> bool:
    """Pulsa la «x» del archivo del cargador (``pt_up1`` o ``pt_up2``)."""
    return bool(nav.js("(() => { const b = document.querySelector('[class*=st-key-%s] [data-testid=stFileChipDeleteBtn]'); if (!b) return false; const i = b.querySelector('button'); (i || b).click(); return true; })()" % cargador))


def lineas(texto: str) -> list[str]:
    return [x.replace("\xa0", " ").strip() for x in texto.split("\n") if x.strip()]


def cifras_ok(texto: str, tarjetas: list) -> list[str]:
    """Las tarjetas de la línea base (etiqueta, valor, sufijo, nota) están en pantalla: la etiqueta, el valor con su sufijo en la línea siguiente y la nota."""
    ls = lineas(texto)
    fallas = []
    for etiqueta, valor, sufijo, nota in tarjetas:
        esperado = (valor + " " + sufijo).strip().replace("\xa0", " ")
        if etiqueta not in ls or ls[ls.index(etiqueta) + 1] != esperado or nota.replace("\xa0", " ") not in ls:
            fallas.append(f"{etiqueta}: esperaba «{esperado}» y «{nota}»")
    return fallas


def tiene_resultado(e: dict) -> bool:
    return bool(e.get("resultado"))


def hay_aviso(e: dict) -> bool:
    return bool(e.get("avisos"))


def foto(nav, destino: Path, nombre: str, alto: int | None = None) -> dict:
    al = float(nav.js("Math.ceil(document.querySelector('[data-testid=\"stMainBlockContainer\"]').getBoundingClientRect().bottom)")) + 30 if alto is None else alto
    al = min(al, 1500)
    nav.cmd("Emulation.setDeviceMetricsOverride", width=F.ANCHO, height=int(max(al, 700)) + 40, deviceScaleFactor=1, mobile=False)
    time.sleep(0.8)
    nav.js("(() => { window.scrollTo(0, 0); return true; })()")
    datos = nav.cmd("Page.captureScreenshot", format="png", clip={"x": 0, "y": 0, "width": F.ANCHO, "height": int(al), "scale": 1})["data"]
    destino.mkdir(parents=True, exist_ok=True)
    (destino / f"{nombre}.png").write_bytes(base64.b64decode(datos))
    print(f"OK   {nombre} {F.ANCHO} x {int(al)}")
    return {"archivo": f"{nombre}.png", "ancho": F.ANCHO, "alto": int(al)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8531)
    ap.add_argument("--debug", type=int, default=9399)
    ap.add_argument("--salida", type=Path, required=True)
    ap.add_argument("--capturas", type=Path, required=True)
    a = ap.parse_args()
    base = json.loads((RAIZ / "docs/ep3/f39_regresion_antes.json").read_text(encoding="utf-8"))
    tarj = lambda seg, modo: base[f"{seg} · {modo}"]["tarjetas"]                                           # noqa: E731
    f = lambda seg: (BASE / seg / "lidar_box.parquet", BASE / seg / "camera_to_lidar_box_association.parquet")      # noqa: E731
    resultados: dict[str, dict] = {}
    caps: list[dict] = []
    nav = C.Navegador(a.debug)

    def caso(nombre: str):
        def deco(fn):
            try:
                detalle = fn()
                fallas = detalle.pop("fallas", [])
                resultados[nombre] = {"ok": not fallas, "fallas": fallas, **detalle}
            except Exception as exc:  # noqa: BLE001
                resultados[nombre] = {"ok": False, "fallas": [f"excepción: {exc!r}"]}
            print(("OK   " if resultados[nombre]["ok"] else "FALLA"), nombre, resultados[nombre]["fallas"][:3])
            return fn
        return deco

    def otro() -> None:
        if not clic(nav, "Cargar otro segmento"):
            raise RuntimeError("no hay botón «Cargar otro segmento»")
        espera(nav, lambda e: e.get("vacio") and not e.get("archivos") and not e.get("resultado"))

    def puntuar_y_esperar() -> dict:
        if not clic(nav, "Puntuar segmento"):
            raise RuntimeError("el botón «Puntuar segmento» no está habilitado")
        return espera(nav, lambda e: tiene_resultado(e) or any(x != CAMBIARON for x in e.get("avisos", [])), 90)          # el aviso «Cambiaron los archivos» ya estaba en pantalla antes de pulsar

    def sube(indice: int, ruta: Path, nombre_esperado: int) -> dict:
        if est(nav).get("expander") is not None:
            abrir_exp(nav)
        subir(nav, indice, ruta)
        return espera(nav, lambda e: len(e.get("archivos", [])) >= nombre_esperado, 60, 1.0)

    try:
        F.abrir(nav, a.puerto, "Puntuar datos nuevos", C.CLAVE["Puntuar datos nuevos"])
        e0 = espera(nav, lambda e: e.get("boton") is not None)

        @caso("0. Inicio: dos cargadores a la vista, botón deshabilitado y ayuda")
        def _():
            fallas = []
            if len(e0["archivos"]) != 0 or e0["boton"]["habilitado"]:
                fallas.append("el botón debería estar deshabilitado sin archivo 1")
            if e0["ayuda"] != "Agregue el archivo 1 para poder puntuar.":
                fallas.append(f"ayuda: {e0['ayuda']!r}")
            if e0["expander"] != {"abierto": True}:
                fallas.append(f"el bloque «Archivos del segmento» debería estar abierto antes de puntuar: {e0['expander']}")
            caps.append(foto(nav, a.capturas, "f39_01_inicio_dos_cargadores", 900))
            return {"fallas": fallas, "ayuda": e0["ayuda"]}

        @caso("1. Archivo 1, luego archivo 2, luego Puntuar (segmento con 1 celda)")
        def _():
            l, s = f(HUECO)
            e1 = sube(0, l, 1)
            fallas = [] if (e1["boton"]["habilitado"] and e1["ayuda"] == AYUDA_1 and not e1["resultado"]) else [f"tras el 1: botón {e1['boton']}, ayuda {e1['ayuda']!r}, resultado {e1['resultado']}"]
            caps.append(foto(nav, a.capturas, "f39_02_solo_archivo_1_antes_de_puntuar", 900))
            e2 = sube(1, s, 2)
            if e2["ayuda"] != AYUDA_2 or e2["resultado"]:
                fallas.append(f"tras el 2: ayuda {e2['ayuda']!r}, resultado {e2['resultado']}")
            e3 = puntuar_y_esperar()
            fallas += cifras_ok(e3["texto"], tarj(HUECO, "archivos 1 y 2"))
            if "hecho" not in e3["pasos"] or "omitido" in e3["pasos"] or e3["expander"] != {"abierto": False}:
                fallas.append(f"pasos o bloque plegable: {e3['pasos']!r} {e3['expander']}")
            if HUECO not in " ".join(e3["lineas_seg"]):
                fallas.append(f"falta el nombre completo del segmento: {e3['lineas_seg']}")
            caps.append(foto(nav, a.capturas, "f39_04_resultado_con_ambos_archivos_1_celda", 1100))
            return {"fallas": fallas, "tarjetas": lineas(e3["texto"])[:14], "lineas_seg": e3["lineas_seg"]}

        @caso("2. Cargar otro segmento limpia todo; archivo 2, luego 1, luego Puntuar (0 celdas)")
        def _():
            otro()
            l, s = f(CERO)
            sube(1, s, 1)
            sube(0, l, 2)
            e3 = puntuar_y_esperar()
            fallas = cifras_ok(e3["texto"], tarj(CERO, "archivos 1 y 2"))
            if CERO not in " ".join(e3["lineas_seg"]) or "Celdas marcadas" not in e3["texto"]:
                fallas.append("el resultado no es el del segmento nuevo")
            caps.append(foto(nav, a.capturas, "f39_07_resultado_con_0_celdas", 1100))
            return {"fallas": fallas, "tarjetas": lineas(e3["texto"])[:14]}

        @caso("3. Solo archivo 1, Puntuar: paso 2 omitido y sin cifras de huecos")
        def _():
            otro()
            l, _s = f(HUECO)
            sube(0, l, 1)
            e3 = puntuar_y_esperar()
            fallas = cifras_ok(e3["texto"], tarj(HUECO, "solo archivo 1"))
            if "omitido: falta el archivo 2" not in e3["pasos"] or "hecho" not in e3["pasos"]:
                fallas.append(f"pasos: {e3['pasos']!r}")
            if "✓" in e3["pasos"].split("Revisar celdas marcadas")[0][-3:]:
                fallas.append("el paso omitido lleva check")
            caps.append(foto(nav, a.capturas, "f39_03_resultado_sin_archivo_2_paso_omitido", 1100))
            return {"fallas": fallas, "pasos": e3["pasos"], "tarjetas": lineas(e3["texto"])[:14]}

        @caso("4. Tras puntuar con solo el 1, agregar el 2: pide volver a puntuar y entonces busca huecos")
        def _():
            _l, s = f(HUECO)
            e1 = sube(1, s, 2)
            fallas = []
            if e1["resultado"] or CAMBIARON not in e1["avisos"]:
                fallas.append(f"debía ocultar el resultado y avisar: resultado {e1['resultado']}, avisos {e1['avisos']}")
            if e1["texto"]:
                fallas.append("quedó texto de un resultado viejo")
            caps.append(foto(nav, a.capturas, "f39_05_aviso_cambiaron_los_archivos", 900))
            e3 = puntuar_y_esperar()
            fallas += cifras_ok(e3["texto"], tarj(HUECO, "archivos 1 y 2"))
            if CAMBIARON in e3["avisos"]:
                fallas.append("quedó el aviso de cambio tras puntuar")
            return {"fallas": fallas}

        @caso("5. Quitar el archivo 2 tras puntuar: el resultado desaparece y avisa")
        def _():
            abrir_exp(nav)
            ok = quitar(nav, "pt_up2")
            e1 = espera(nav, lambda e: not e.get("resultado") and CAMBIARON in e.get("avisos", []))
            fallas = [] if (ok and not e1["resultado"] and CAMBIARON in e1["avisos"] and e1["ayuda"] == AYUDA_1) else [f"botón quitar {ok}, resultado {e1['resultado']}, avisos {e1['avisos']}, ayuda {e1['ayuda']!r}"]
            e3 = puntuar_y_esperar()
            fallas += cifras_ok(e3["texto"], tarj(HUECO, "solo archivo 1"))
            return {"fallas": fallas}

        @caso("6. Cambiar el 1 por otro segmento tras puntuar; con el 2 del anterior: error con los dos ids; al corregir, puntúa")
        def _():
            _l, s = f(HUECO)
            copia = Path(tempfile.mkdtemp(prefix="f39_copia_")) / "asociacion_hueco_copia.parquet"          # el mismo archivo 2 con otro nombre: el navegador no avisa un cambio si se vuelve a elegir exactamente el mismo archivo
            copia.write_bytes(s.read_bytes())
            sube(1, copia, 2)                                                     # el 2 del segmento con hueco otra vez
            espera(nav, lambda e: e.get("ayuda") == AYUDA_2)          # el servidor ya recibió el archivo 2 (la «x» del navegador aparece antes de que termine de subir)
            l_otro, s_otro = f(CERO)
            subir(nav, 0, l_otro)
            time.sleep(3.5)                                                       # que el servidor reciba el archivo 1 nuevo antes de seguir
            e1 = espera(nav, lambda e: CAMBIARON in e.get("avisos", []) and not e.get("resultado"))
            fallas = [] if (not e1["resultado"] and CAMBIARON in e1["avisos"]) else [f"tras cambiar el 1: resultado {e1['resultado']}, avisos {e1['avisos']}"]
            e2 = puntuar_y_esperar()
            texto_error = " ".join(e2["avisos"])
            if e2["resultado"] or HUECO not in texto_error or CERO not in texto_error or "Archivo 1:" not in texto_error or "Archivo 2:" not in texto_error:
                fallas.append(f"el error debía traer los dos ids completos: {e2['avisos']}")
            caps.append(foto(nav, a.capturas, "f39_06_error_segmentos_distintos_dos_ids", 900))
            sube(1, s_otro, 2)                                                    # corregir: el 2 del mismo segmento que el 1
            e3 = espera(nav, lambda e: not any(HUECO in x for x in e.get("avisos", [])))
            if any(HUECO in x for x in e3["avisos"]):
                fallas.append(f"quedó el error del intento anterior: {e3['avisos']}")
            e4 = puntuar_y_esperar()
            fallas += cifras_ok(e4["texto"], tarj(CERO, "archivos 1 y 2"))
            return {"fallas": fallas, "error": e2["avisos"]}

        @caso("7. Archivo que no es parquet: error claro, sin resultado")
        def _():
            otro()
            with tempfile.TemporaryDirectory(prefix="f39_malo_") as tmp:
                malo = Path(tmp) / "no_es_parquet.parquet"
                malo.write_text("esto no es un parquet", encoding="utf-8")
                sube(0, malo, 1)
                e1 = puntuar_y_esperar()
            fallas = [] if (not e1["resultado"] and any("no es un parquet válido" in x for x in e1["avisos"])) else [f"avisos {e1['avisos']}"]
            return {"fallas": fallas, "avisos": e1["avisos"]}

        @caso("8. Cargar otro segmento y repetir (el más grande, 7.854 cajas)")
        def _():
            quitar(nav, "pt_up1")                                                  # tras un error no hay «Cargar otro segmento»: se quita el archivo inválido con su «x»
            espera(nav, lambda e: not e.get("archivos") and not any("parquet" in x for x in e.get("avisos", [])))
            l, s = f(GRANDE)
            sube(0, l, 1)
            sube(1, s, 2)
            e3 = puntuar_y_esperar()
            fallas = cifras_ok(e3["texto"], tarj(GRANDE, "archivos 1 y 2"))
            if any("parquet" in x for x in e3["avisos"]):
                fallas.append("quedó el error del archivo inválido")
            return {"fallas": fallas, "tarjetas": lineas(e3["texto"])[:14]}

        @caso("9. Botón de ejemplo de desarrollo")
        def _():
            otro()
            if not clic(nav, "Usar un segmento de desarrollo de ejemplo"):
                raise RuntimeError("no hay botón de ejemplo")
            e1 = espera(nav, lambda e: tiene_resultado(e) or hay_aviso(e), 60)
            ej = base["ejemplo de desarrollo 911012534050"]["tarjetas"]
            fallas = cifras_ok(e1["texto"], ej)
            if "ejemplo de desarrollo" not in e1["titulo"] or CAMBIARON in e1["avisos"]:
                fallas.append(f"título {e1['titulo']!r}, avisos {e1['avisos']}")
            caps.append(foto(nav, a.capturas, "f39_08_ejemplo_de_desarrollo", 1100))
            return {"fallas": fallas, "tarjetas": lineas(e1["texto"])[:14]}

        @caso("10. Bloque «Segmentos puntuados en esta sesión» del Resumen: una fila por segmento, la repetida se reemplaza")
        def _():
            ok = nav.js("(() => { const a = Array.from(document.querySelectorAll('a')).find(x => x.href === %s); if (!a) return false; a.click(); return true; })()" % json.dumps(C.url(a.puerto, "Resumen")))
            e1 = espera(nav, lambda e: bool(e.get("sesion")), 30)
            filas = [l for l in lineas(e1["sesion"]) if l.startswith("…")]
            ids = [x.split()[0] for x in filas]
            fallas = []
            if not ok or len(ids) != len(set(ids)):
                fallas.append(f"filas repetidas o sin Resumen: {filas}")
            corto = lambda s: "…" + s[:12][-6:]                                                           # noqa: E731
            if set(ids) != {corto(HUECO), corto(CERO), corto(GRANDE)}:
                fallas.append(f"se esperaban las filas {sorted({corto(HUECO), corto(CERO), corto(GRANDE)})} y hay {ids}")
            return {"fallas": fallas, "filas": filas, "bloque": e1["sesion"][:400]}
    finally:
        nav.cerrar()
    a.salida.write_text(json.dumps({"pruebas": resultados, "capturas": caps}, indent=1, ensure_ascii=False), encoding="utf-8")
    ok = sum(1 for r in resultados.values() if r["ok"])
    print(f"{ok} de {len(resultados)} pruebas de estado correctas; capturas: {len(caps)}")


if __name__ == "__main__":
    main()
