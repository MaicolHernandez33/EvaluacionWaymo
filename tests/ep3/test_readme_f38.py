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
    assert "Pendiente: completar con la retroalimentación del docente" not in texto                      # F40: la sección 17 ya no muestra el aviso de pendiente


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
        s17 = _sec(_texto(), "## 17.")
        assert "Pendiente" not in s17 and "Retroalimentación recibida" not in s17                   # F40: sin retroalimentación escrita no hay texto de relleno ni aviso de pendiente
        assert "Esta tabla recoge las mejoras documentadas en el repositorio" in s17
    assert e["caso_acordado"] in _texto()


# ------------------------------------------------------------------------------------------------------------ pruebas citadas
def test_el_numero_de_pruebas_de_ep3_del_readme_es_el_recolectado() -> None:
    conteo = json.loads((R / "data/08_reporting_ep3/pruebas_ep3_conteo.json").read_text(encoding="utf-8"))
    assert f"{_miles(conteo['recolectadas_ep3'])} pruebas recolectadas en `tests/ep3`" in _texto(), "regenerar el README (scripts/generar_readme.py) tras contar las pruebas"



# ------------------------------------------------------------------------------------------------------------ F40: prueba con segmentos nuevos, cifras de 8.1, árbol, notebooks y tope de líneas
def _prueba() -> dict:
    return json.loads((R / "docs/ep3/prueba_segmentos_nuevos.json").read_text(encoding="utf-8"))


def test_el_readme_no_supera_800_lineas_ni_deja_marcadores_de_relleno() -> None:
    texto = _texto()
    assert len(texto.splitlines()) <= 800
    assert not re.search(r"\bTODO\b|\bPendiente\b|\bpendiente:|xxx|\[nombre del servicio\]", texto)
    limpio = re.sub(r"</?(details|summary)>|<=", "", texto)
    assert "<" not in limpio.replace("<br>", "")
    for linea in texto.splitlines():
        if "borrador" in linea.lower():
            assert "modo publicado" in linea and "sin activar" in linea                                # la única mención es el aviso del modo publicado (docs/despliegue.json)


def test_la_prueba_con_segmentos_nuevos_del_readme_sale_del_json_y_no_inventa_cifras() -> None:
    d = _prueba()
    texto = _texto()
    sub = texto.split("### Prueba con segmentos nuevos")[1].split("\n## 17.")[0]
    assert len(d["segmentos"]) == 4 and "prueba de funcionamiento" in sub.lower() and "no una validación estadística" in sub
    for s in d["segmentos"]:
        assert f"`{s['segmento']}`" in sub and s["id_abreviado"] in sub and _miles(s["cajas_puntuadas"]) in sub, s["segmento"]
        assert s["celdas_marcadas"] == len(s["celdas"]) and s["sha256"]
    marcadas = [s for s in d["segmentos"] if s["celdas_marcadas"]]
    assert len(marcadas) == 1 and f"{len(marcadas)} de {len(d['segmentos'])}" in sub
    z = marcadas[0]["celdas"][0]
    assert _miles(z["cajas_en_rango"]) in sub and _miles(z["cajas_afectadas"]) in sub and _miles(marcadas[0]["sin_pareja_en_celdas_marcadas"]) in sub
    assert "Puntuar segmento" in sub and "cualquier orden" in sub and "archivo 2 primero" not in texto    # el flujo de F39 reemplaza el orden obligatorio de F37
    assert "sigue sin ejecutarse" in sub and "validación externa" in sub


def test_el_json_de_la_prueba_coincide_con_los_archivos_de_entrada() -> None:
    base = R / "datos_demo/candidatos"
    if not base.exists():
        pytest.skip("datos_demo/ no está (no se versiona)")
    import hashlib

    for s in _prueba()["segmentos"]:
        for nombre, h in s["sha256"].items():
            ruta = base / s["segmento"] / nombre
            if ruta.exists():
                assert hashlib.sha256(ruta.read_bytes()).hexdigest() == h, ruta


def test_el_recuadro_de_8_1_usa_los_auc_calculados_de_los_datos() -> None:
    import pandas as pd
    from sklearn.metrics import roc_auc_score

    cajas = pd.read_parquet(R / "data/09_app_ep3/cajas_oof.parquet", columns=["grupo", "sin_camara", "score"])
    sec = _texto().split("### 8.1 ")[1].split("### 8.2 ")[0]
    recuadro = sec.split("> Optimizar mejora")[0]
    for x in (cajas, cajas[cajas["grupo"] == "train"], cajas[cajas["grupo"] == "test"]):
        assert f"{roc_auc_score(x['sin_camara'], x['score']):.3f}".replace(".", ",") in recuadro
    assert "StratifiedGroupKFold" in recuadro and "`tiene_camara`" in recuadro and "`sin_camara`" in recuadro
    assert recuadro.count("| EP2:") == 1 and recuadro.count("| EP3:") == 1 and "no son comparables" in recuadro
    assert "recuadro de [8.1](#" in _sec(_texto(), "### 8.3") and "sección [8.1](#" in _sec(_texto(), "## 2.")                       # referencias cruzadas desde 8.3 y desde los KPI de la sección 2
    assert "`GroupKFold` de 5" not in _texto()                                                          # el README de F38 describía mal los folds externos de EP3


def test_la_tabla_de_notebooks_lista_los_archivos_reales_en_su_orden() -> None:
    from readme_f38 import ORDEN_NB

    reales = sorted(p.stem for p in (R / "notebooks").glob("*.ipynb"))
    assert sorted(ORDEN_NB) == reales and len(reales) == 19
    sec14 = _sec(_texto(), "## 14.")
    enlaces = re.findall(r"\[`([^`]+)\.ipynb`\]\(notebooks/", sec14)
    assert enlaces == ORDEN_NB
    for stem in enlaces:
        assert (R / "notebooks" / f"{stem}.ipynb").exists()
    assert "salidas guardadas" in sec14 and "sin salidas guardadas" in sec14                            # solo se afirma ejecución donde los archivos o los registros lo muestran


def test_el_arbol_del_readme_cubre_cada_carpeta_de_la_raiz() -> None:
    sec14 = _sec(_texto(), "## 14.")
    arbol = sec14.split("waymo-evaluacion/")[1].split("```")[0]
    ocultos = {".git", ".venv", "__pycache__", ".pytest_cache", ".ipynb_checkpoints", ".viz", ".mypy_cache", "node_modules"}
    for p in R.iterdir():
        if p.name not in ocultos and not p.name.startswith(".coverage") and p.name != "info.log":
            assert p.name in arbol, p.name


def test_la_seccion_17_agrega_las_opciones_del_docente_y_la_validacion_nueva() -> None:
    import readme_f38 as rm

    s17 = _sec(_texto(), "## 17.")
    opciones = rm.entradas().get("opciones_docente", "")
    assert opciones and "tres opciones" in opciones and "el esquema propuesto por el equipo" in opciones
    assert "El docente ofreció tres opciones ante el segmento anómalo" in s17 and "El equipo adoptó su esquema" in s17
    assert "prueba_segmentos_nuevos.json" in s17 and "validación externa sellada" in s17


def test_la_remedicion_de_las_pruebas_del_readme_es_la_registrada() -> None:
    ruta = R / "data/08_reporting_ep3/pruebas_ep2_remedicion.json"
    if not ruta.exists():
        pytest.skip("sin remedición de EP2 registrada")
    q = json.loads(ruta.read_text(encoding="utf-8"))
    s14 = _sec(_texto(), "## 14.")
    assert f"{q['pasadas']} pasadas, {q['falladas']} falladas" in s14
    r = json.loads((R / "data/08_reporting_ep3/pruebas_ep3_resultado.json").read_text(encoding="utf-8"))
    assert f"{r['pasadas']} pasadas, {r['falladas']} falladas" in s14
