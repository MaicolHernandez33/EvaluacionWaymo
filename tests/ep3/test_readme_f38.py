"""F38: el README final (informe técnico) de EP3 y la Evaluación Final Transversal.

Comprueba, sin ejecutar ningún generador ni reescribir nada (solo lee ``README.md``): que las cifras de la portada y de la sección 16 son las que calcula la página (se importan sus funciones), que todos los
enlaces internos, de archivos y de imágenes existen, que los comandos de «Cómo verlo» apuntan a archivos reales (y que la aplicación arranca con el comando indicado), que ``docs/despliegue.json`` produce
el texto correcto con y sin URL y que las notas de corrección del texto de EP2 están. El README se genera con ``scripts/generar_readme.py``; si estas pruebas fallan tras tocar datos, regenerarlo.
"""
from __future__ import annotations

import json
import re
import socket
import subprocess
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

import pytest

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "src"))
sys.path.insert(0, str(R / "scripts" / "ep3"))
README = R / "README.md"
HAY = README.exists() and (R / "data/09_app_ep3/cajas_oof.parquet").exists() and (R / "artefactos_ep3/f6_tabla_seleccion.csv").exists()
pytestmark = pytest.mark.skipif(not HAY, reason="faltan el README o los datos de la página")


def _texto() -> str:
    return README.read_text(encoding="utf-8")


def _slug(t: str) -> str:
    t = unicodedata.normalize("NFC", t.lower())
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", t).strip())


def _sec(texto: str, titulo: str) -> str:
    m = re.search(rf"^{re.escape(titulo)}.*?(?=^## |\Z)", texto, flags=re.S | re.M)
    assert m, titulo
    return m.group(0)


def _miles(x) -> str:
    return f"{int(round(float(x))):,}".replace(",", ".")


# ------------------------------------------------------------------------------------------------------------ cifras = las de la página
def test_las_cifras_de_la_portada_y_de_la_seccion_16_son_las_que_calcula_la_pagina() -> None:
    from waymo_evaluacion.ep3 import app_logica as A

    D = A.cargar_datos(R / "data/09_app_ep3")
    det = json.loads((R / "data/06_models_ep3/detector_params_v3.json").read_text(encoding="utf-8"))
    rangos = {int(k): tuple(v) for k, v in det["rangos"].items()}
    r = A.inicio_resumen(D)
    aud = A.resumen_auditoria(A.matriz_calor(D["celdas"], det["min_cajas"]), D["lista_A"])
    _, en_cola = A.cola_prioritaria(D["cajas"], rangos)
    cic = A.datos_ciclistas(D["evidencia"].get("posthoc__equidad"))
    texto = _texto()
    portada = texto.split("\n## 1. Resumen")[0]
    s16 = _sec(texto, "## 16.")
    pct = lambda x: f"{x * 100:.1f}".replace(".", ",") + " %"                                                   # noqa: E731
    for esperado in (_miles(r["cajas"]), pct(r["prevalencia"]), pct(r["fraccion_80_dos_pasos"]), pct(r["fraccion_80_un_paso"]), _miles(r["horas_sin_orden"]) + " h", _miles(r["horas_un_paso"]) + " h",
                     _miles(r["horas_dos_pasos"]) + " h", pct(cic["ciclista"]), pct(cic["peaton"]), _miles(cic["positivos"]) + " casos en " + _miles(cic["segmentos"]) + " segmentos"):
        assert esperado in portada, esperado
    assert f"{A.SUPUESTO_SEGUNDOS} s por caja" in portada and "supuesto" in portada
    for etiqueta, valor in (("Segmentos de desarrollo", r["segmentos"]), ("Celdas segmento × cámara", aud["celdas_total"]), ("Celdas marcadas por el detector", aud["celdas_marcadas"]),
                            ("Cajas en las celdas marcadas", aud["cajas_afectadas"]), ("Cajas en la cola", en_cola), ("Cajas de peatones y ciclistas (población principal)", r["cajas"])):
        assert f"| {etiqueta} | {_miles(valor)} |" in s16, etiqueta


def test_los_numeros_de_la_correccion_54_8_y_35_8_salen_de_los_datos() -> None:
    import pandas as pd

    c = pd.read_parquet(R / "data/09_app_ep3/cajas_oof.parquet", columns=["seg", "grupo", "sin_camara", "en_hueco"])
    t = c[c["grupo"] == "test"]
    seg = "257766998801"
    pos, anom, celda = int(t["sin_camara"].sum()), int(t[t["seg"] == seg]["sin_camara"].sum()), int(t[(t["seg"] == seg) & t["en_hueco"]]["sin_camara"].sum())
    texto = _texto()
    assert (pos, anom, celda) == (3734, 2046, 1338)
    nota = f"{anom / pos * 100:.1f}".replace(".", ",") + f" % es la parte del segmento `{seg}` en los positivos del test ({_miles(anom)} de {_miles(pos)})"
    assert texto.count(nota) == 2                                                                              # secciones 1 y 11
    assert f"explica el {celda / pos * 100:.1f}".replace(".", ",") + f" % ({_miles(celda)} de {_miles(pos)})" in texto


def test_las_notas_de_correccion_del_texto_de_ep2_estan() -> None:
    texto = _texto()
    assert texto.count("la única prueba ciega son los segmentos nuevos") >= 2 and "datos de desarrollo" in texto
    assert "**Dos resultados con k = 2, dos poblaciones.**" in texto and "68.555 filas" in texto and "80.571 cajas" in texto and "sin oclusión" in texto
    assert "Parcial N°2" not in texto.split("\n## 1. Resumen")[0]
    assert "Pendiente: completar con la retroalimentación del docente" in texto or json.loads((R / "docs/ep3/readme_entradas.json").read_text(encoding="utf-8")).get("retroalimentacion_ep1")


# ------------------------------------------------------------------------------------------------------------ enlaces
def test_todos_los_enlaces_internos_de_archivos_e_imagenes_existen() -> None:
    texto = _texto()
    anclas = {_slug(re.sub(r"^#+ ", "", l)) for l in texto.splitlines() if l.startswith(("## ", "### "))}
    faltan = []
    for m in re.finditer(r"!?\[[^\]]*\]\(([^)\s]+)\)", texto):
        destino = m.group(1)
        if destino.startswith(("http://", "https://", "mailto:")):
            continue
        if destino.startswith("#"):
            if destino[1:] not in anclas:
                faltan.append(destino)
        elif not (R / destino.split("#")[0]).exists():
            faltan.append(destino)
    assert not faltan, faltan
    assert len(re.findall(r"!\[[^\]]*\]\(images/app/[^)]+\)", texto)) == 4                                     # las capturas de la sección 16


def test_los_encabezados_de_ep3_estan_y_las_secciones_1_a_15_conservan_su_ancla() -> None:
    texto = _texto()
    titulos = [l for l in texto.splitlines() if l.startswith("## ")]
    assert [int(t.split(".")[0][3:]) for t in titulos] == list(range(1, 18))
    for sub in ("### 8.1 ", "### 8.2 ", "### 8.3 ", "### 12.1 "):
        assert sub in texto
    for n in ("1. Resumen", "8. Modelos supervisados", "12. Interpretación y recomendaciones"):
        assert f"## {n}" in texto
    assert not [l for l in texto.splitlines() if l.startswith(("# ",)) and "Parcial" in l]


# ------------------------------------------------------------------------------------------------------------ comandos de «Cómo verlo»
def test_los_comandos_de_como_verlo_apuntan_a_archivos_que_existen() -> None:
    tabla = _texto().split("**Cómo verlo**")[1].split("\n\n")[1]
    assert "app\\lanzar.py" in tabla and "arrancar_app.bat" in tabla and "verificar_congelados.py" in tabla and "pytest tests/ep3" in tabla
    for ruta in ("app/lanzar.py", "app/app.py", "scripts/ep3/arrancar_app.bat", "scripts/verificar_congelados.py", "notebooks/10_evaluacion_final_sin_camara.ipynb", "tests/ep3"):
        assert (R / ruta).exists(), ruta


def test_la_aplicacion_arranca_con_el_comando_del_readme() -> None:
    if not (R / "data/06_models_ep3/modelo_final_v3.joblib").exists():
        pytest.skip("falta la solución congelada")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        puerto = s.getsockname()[1]
    # mismo comando del README (el puerto cambia para no chocar con una página ya abierta)
    proc = subprocess.Popen([sys.executable, str(R / "app/lanzar.py"), "--server.address", "localhost", "--server.port", str(puerto), "--server.headless", "true", "--browser.gatherUsageStats", "false"],
                            cwd=R, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ok = False
        t0 = time.time()
        while time.time() - t0 < 90 and proc.poll() is None:
            try:
                ok = urllib.request.urlopen(f"http://127.0.0.1:{puerto}/_stcore/health", timeout=2).status == 200
                if ok:
                    break
            except Exception:  # noqa: BLE001
                time.sleep(1)
        assert ok, "la aplicación no respondió en 90 s con el comando del README"
    finally:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/F", "/T"], capture_output=True) if sys.platform == "win32" else proc.terminate()


# ------------------------------------------------------------------------------------------------------------ docs/despliegue.json
def test_despliegue_json_sin_url_dice_en_preparacion_y_con_url_enlaza(monkeypatch: pytest.MonkeyPatch) -> None:
    import readme_f38 as rm

    base = json.loads((R / "docs/despliegue.json").read_text(encoding="utf-8"))
    assert set(base) == {"estado", "url", "fecha", "modo"}
    from waymo_evaluacion.ep3.app_logica import MODO_DESPLIEGUE

    assert base["modo"] == MODO_DESPLIEGUE
    monkeypatch.setattr(rm, "despliegue", lambda: {**base, "url": ""})
    sin = rm.como_verlo()
    assert "Despliegue en AWS Academy: en preparación" in sin and "http" not in sin.split("Aplicación desplegada")[1]
    s16 = rm.sec_16(lambda n, pie: f"![{pie}](images/{n})", _slug)
    assert "Dirección:" not in s16 and f"**{base['estado']}**" in s16
    monkeypatch.setattr(rm, "despliegue", lambda: {**base, "url": "https://ejemplo.invalido/lente", "estado": "desplegada"})
    con = rm.como_verlo()
    assert "[https://ejemplo.invalido/lente](https://ejemplo.invalido/lente)" in con and "en preparación" not in con
    assert "Dirección: [https://ejemplo.invalido/lente]" in rm.sec_16(lambda n, pie: f"![{pie}](images/{n})", _slug)


def test_las_entradas_vacias_omiten_su_parte_y_el_readme_lo_dice() -> None:
    import readme_f38 as rm

    e = rm.entradas()
    assert set(e) >= {"retroalimentacion_ep1", "retroalimentacion_ep2", "caso_acordado"}
    if not e["retroalimentacion_ep1"] and not e["retroalimentacion_ep2"]:
        assert "**Pendiente: completar con la retroalimentación del docente** (EP1 y EP2)" in _texto()
    assert e["caso_acordado"] in _texto()


# ------------------------------------------------------------------------------------------------------------ pruebas citadas
def test_el_numero_de_pruebas_de_ep3_del_readme_es_el_recolectado() -> None:
    conteo = json.loads((R / "data/08_reporting_ep3/pruebas_ep3_conteo.json").read_text(encoding="utf-8"))
    assert f"{_miles(conteo['recolectadas_ep3'])} pruebas recolectadas en `tests/ep3`" in _texto(), "regenerar el README (scripts/generar_readme.py) tras contar las pruebas"
