"""F36: Ética y límites y Ayuda y glosario rediseñadas (regla de uso arriba, tarjetas, tres pasos con enlaces, glosario con buscador y grupos, preguntas frecuentes de siempre) y el modo de despliegue.

Cubre la regresión de textos (cada frase de antes sigue, con la misma redacción, salvo las excepciones documentadas en ``etica_ayuda.FRASES_AJUSTADAS``), el buscador del glosario, los tres textos que dependen de
``MODO_DESPLIEGUE`` (por defecto ``local``, con los textos de antes), los enlaces de los tres pasos y las cifras compartidas. Escribe solo en ``tmp_path``.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import pytest

from tests.ep3.test_app import ir_a, textos
from tests.ep3.test_pagina_f21 import HAY_REAL, _abrir_real
from tests.ep3.test_pagina_f24 import _abrir, _sin_css, entorno  # noqa: F401  (``entorno`` es la fixture del módulo de F24)

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))
ANTES = R / "tests/ep3/datos_f36/textos_antes.json"


def _n(t: str) -> str:
    """Minúsculas, sin tildes ni signos: compara el contenido de las palabras y no la puntuación (los dos puntos de una frase partida pasan a punto)."""
    t = "".join(c for c in unicodedata.normalize("NFD", t.replace("\xa0", " ").lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9ñ%]+", " ", t)).strip()


def _visible(at) -> str:
    partes = [m.value for m in at.markdown] + [c.value for c in at.caption] + [e.label for e in at.expander] + [m.value for e in at.expander for m in e.markdown]
    for t in at.table:
        partes += [str(x) for x in t.value.to_numpy().ravel()]
    return re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", " ", " ".join(partes), flags=re.S)).replace("\xa0", " ").replace("**", "")


# ------------------------------------------------------------------------------------------------------------ regresión de textos (regla 6)
@pytest.mark.skipif(not (HAY_REAL and ANTES.exists()), reason="faltan los datos de la página o el archivo de textos de antes")
def test_regresion_de_textos_cada_frase_de_antes_sigue_o_esta_en_las_excepciones(monkeypatch: pytest.MonkeyPatch) -> None:
    from waymo_evaluacion.ep3.etica_ayuda import FRASES_AJUSTADAS

    antes = json.loads(ANTES.read_text(encoding="utf-8"))
    nuevo = {}
    at = _abrir_real(monkeypatch, "Ética y límites")
    nuevo["Ética y límites"] = _n(_visible(at))
    ir_a(at, "Ayuda y glosario")
    nuevo["Ayuda y glosario"] = _n(_visible(at))
    prefijos = [_n(k.split("{")[0])[:45] for k in FRASES_AJUSTADAS]
    faltan = []
    for pagina, datos in antes.items():
        for frase in [x for fr in datos["frases"] for x in re.split(r" - (?=[A-ZÁÉÍÓÚ])", fr)]:                    # las viñetas de «Uso» venían unidas en una frase
            f = re.sub(r"^(#+ |- )", "", frase)
            f = re.sub(r"^(Cola de revisión|Auditoría de cámaras): ", "", f)                                  # las líneas de «Uso» pasan a tarjetas con su título aparte
            f = re.sub(r"^(Propósito|Datos y licencia|Desempeño|Límites conocidos|Consideraciones éticas|Dónde corre) ", "", f)            # en la captura de antes cada ficha empezaba con su título
            if f.startswith(("Término Definición", "Celda Una", "Caja Un", "Par 2D La")) or re.match(r"^(Caja|Par 2D|Celda|Hueco|Cola|Presupuesto|Cobertura|Intervalo de confianza|Post hoc|En muestra|Sin prueba ciega) [A-ZÁÉÍÓÚ]", f):
                continue                                                                                          # las filas del glosario se comprueban una por una en otra prueba
            if f.startswith(("Flujo de tres capas:", "Uso")) or _n(f) == "":
                continue
            if _n(f) in nuevo[pagina] or _n(f) in nuevo["Ética y límites"] + " " + nuevo["Ayuda y glosario"]:
                continue
            if any(_n(f).startswith(p) for p in prefijos if p):
                continue
            faltan.append(f"{pagina}: {f[:110]}")
    assert not faltan, faltan[:8]


@pytest.mark.skipif(not (HAY_REAL and ANTES.exists()), reason="faltan los datos de la página o el archivo de textos de antes")
def test_las_11_definiciones_del_glosario_y_las_preguntas_son_las_de_antes(monkeypatch: pytest.MonkeyPatch) -> None:
    from waymo_evaluacion.ep3.app_logica import GLOSARIO, preguntas_frecuentes

    antes = json.loads(ANTES.read_text(encoding="utf-8"))["Ayuda y glosario"]
    tabla_antes = _n(next(b for b in antes["bloques"] if b.startswith("Término Definición")))
    assert len(GLOSARIO) == 11 and all(_n(t) in tabla_antes and _n(d) in tabla_antes for t, d in GLOSARIO)         # las 11 definiciones, palabra por palabra
    at = _abrir_real(monkeypatch, "Ayuda y glosario")
    ir_a(at, "Ayuda y glosario")
    pagina = _n(_visible(at))
    assert all(_n(d) in pagina for _, d in GLOSARIO)
    for q, a in preguntas_frecuentes(None)[:1] + preguntas_frecuentes(None)[1:2] + preguntas_frecuentes(None)[3:4]:
        assert _n(q) in pagina and _n(a) in " ".join(_n(b) for b in antes["bloques"])                              # preguntas y respuestas de siempre (las que no llevan cifras salen idénticas)
    assert [e.label for e in at.expander] == [q for q, _ in preguntas_frecuentes(None)]


# ------------------------------------------------------------------------------------------------------------ buscador del glosario
def test_el_buscador_filtra_por_termino_por_definicion_por_grupo_y_combinado() -> None:
    from waymo_evaluacion.ep3.etica_ayuda import GRUPO_TODOS, filtrar_glosario, grupos_del_glosario

    todos = filtrar_glosario()
    assert len(todos) == 11 and [t["termino"] for t in todos][:3] == ["Caja", "Par 2D", "Celda"]
    assert [t["termino"] for t in filtrar_glosario("hueco")] == ["Par 2D", "Hueco", "Cola"] or "Hueco" in [t["termino"] for t in filtrar_glosario("hueco")]
    assert [t["termino"] for t in filtrar_glosario("LIDAR")] == ["Caja"]                                       # por parte de una definición, sin distinguir mayúsculas
    assert [t["termino"] for t in filtrar_glosario("analisis")] == ["Post hoc"]                                # sin distinguir tildes («análisis»)
    assert [t["termino"] for t in filtrar_glosario(grupo="Rigor")] == ["Intervalo de confianza", "Post hoc", "En muestra", "Sin prueba ciega"]
    assert [t["termino"] for t in filtrar_glosario(grupo="Revisión")] == ["Cola", "Presupuesto", "Cobertura"] and [t["termino"] for t in filtrar_glosario(grupo="Datos")] == ["Caja", "Par 2D", "Celda", "Hueco"]
    assert [t["termino"] for t in filtrar_glosario("muestra", "Rigor")] == ["Intervalo de confianza", "En muestra"] or {"En muestra"} <= {t["termino"] for t in filtrar_glosario("muestra", "Rigor")}
    assert filtrar_glosario("muestra", "Datos") == [] and filtrar_glosario("zzzzz") == []                       # grupo y búsqueda combinados; sin coincidencias
    assert filtrar_glosario(grupo=GRUPO_TODOS) == todos and filtrar_glosario(grupo=None) == todos
    assert grupos_del_glosario() == ["Todos", "Datos", "Revisión", "Rigor"]


def test_un_termino_nuevo_del_glosario_aparece_bajo_otros() -> None:
    from waymo_evaluacion.ep3.etica_ayuda import filtrar_glosario, grupos_del_glosario
    from waymo_evaluacion.ep3.app_logica import GLOSARIO

    extendido = [*GLOSARIO, ("Término nuevo", "Algo agregado después.")]
    assert grupos_del_glosario(extendido)[-1] == "Otros" and [t["termino"] for t in filtrar_glosario(grupo="Otros", glosario=extendido)] == ["Término nuevo"]


def test_la_pagina_filtra_el_glosario_y_dice_cuando_no_hay_coincidencias(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Ayuda y glosario")
    assert _visible(at).count("Rigor") >= 4 and len(at.text_input) == 1
    at.text_input(key="gl_busqueda").set_value("cola").run()
    html = " ".join(m.value for m in at.markdown)
    assert not at.exception and html.count('class="d"') == len(__import__("waymo_evaluacion.ep3.etica_ayuda", fromlist=["x"]).filtrar_glosario("cola"))
    at.text_input(key="gl_busqueda").set_value("zzzz").run()
    assert "Ningún término coincide con la búsqueda." in _visible(at) and ' class="d"' not in " ".join(m.value for m in at.markdown)
    at.text_input(key="gl_busqueda").set_value("").run()
    at.get("pills")[0].set_value("Rigor").run()
    assert not at.exception and " ".join(m.value for m in at.markdown).count('class="d"') == 4


# ------------------------------------------------------------------------------------------------------------ modo de despliegue (sección 3)
def test_por_defecto_el_modo_es_local_con_los_textos_de_siempre() -> None:
    from waymo_evaluacion.ep3 import app_logica as A

    assert A.MODO_DESPLIEGUE == "local" and A.entorno_pagina() == "local"
    assert A.texto_entorno("donde_corre") == "Solo en este equipo (localhost), sin conexión a internet. No debe exponerse en una red sin autenticación."
    assert A.texto_entorno("consideracion_etica") == "Las tablas locales tienen identificadores de objeto y marcas de tiempo. Nada se guarda ni se envía."
    assert A.texto_entorno("faq_archivos") == "No. Nada se guarda ni se envía: «Puntuar datos nuevos» procesa el archivo en memoria y la aplicación no hace ninguna conexión a internet."
    assert (A.texto_entorno("puntuar_etiqueta"), A.texto_entorno("puntuar_etiqueta_2")) == ("Procesamiento local y en memoria", "No se guarda nada") and A.texto_entorno("borrador") == ""


def test_los_cuatro_textos_cambian_con_la_constante_y_salen_de_un_solo_lugar(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    from waymo_evaluacion.ep3 import app_logica as A

    monkeypatch.setattr(A, "MODO_DESPLIEGUE", "publicado")
    assert A.entorno_pagina() == "publicado" and A.texto_entorno("borrador") == "borrador: verificar"
    etica = _sin_css(textos(_abrir(entorno, monkeypatch, "Ética y límites")))
    assert "En un servidor de AWS (instancia EC2 de AWS Academy" in etica and "los procesa en memoria durante la sesión, no los escribe a disco" in etica
    assert etica.count("borrador: verificar") == 2 and "Solo en este equipo (localhost)" not in etica and "Nada se guarda ni se envía" not in etica
    ayuda = _sin_css(textos(_abrir(entorno, monkeypatch, "Ayuda y glosario")))
    ayuda += " ".join(m.value for e in _abrir(entorno, monkeypatch, "Ayuda y glosario").expander for m in e.markdown)
    assert "Allí se procesan en memoria durante la sesión: no se escriben a disco ni se registra su contenido" in ayuda
    puntuar = _sin_css(textos(_abrir(entorno, monkeypatch, "Puntuar datos nuevos")))
    assert "Procesamiento en el servidor y en memoria" in puntuar and "Procesamiento local y en memoria" not in puntuar
    monkeypatch.setattr(A, "MODO_DESPLIEGUE", "local")
    assert A.entorno_pagina() == "local" and A.texto_entorno("borrador") == ""                                  # volver a «local» devuelve los textos de siempre


def test_ninguna_pagina_escribe_a_mano_los_textos_que_dependen_del_modo() -> None:
    """Los textos de despliegue salen solo de ``texto_entorno``: no hay copias escritas en ``app/`` ni en ``etica_ayuda.py``."""
    from waymo_evaluacion.ep3.app_logica import TEXTOS_ENTORNO

    fuentes = " ".join(p.read_text(encoding="utf-8") for p in [*sorted((R / "app").rglob("*.py")), R / "src/waymo_evaluacion/ep3/etica_ayuda.py"])
    for modo in TEXTOS_ENTORNO.values():
        for clave, texto in modo.items():
            if texto:
                assert texto not in fuentes, clave
    assert "Procesamiento local y en memoria" not in fuentes and "No se guarda nada" not in fuentes


# ------------------------------------------------------------------------------------------------------------ enlaces y cifras
def test_los_enlaces_de_los_tres_pasos_llegan_a_la_pagina_correcta(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    from waymo_evaluacion.ep3.app_logica import ARCHIVO_PAGINA, URL_PAGINA
    from waymo_evaluacion.ep3.etica_ayuda import PASOS

    at = _abrir(entorno, monkeypatch, "Ayuda y glosario")
    enlaces = [(p.proto.page, p.proto.label) for p in at.get("page_link")]
    assert enlaces == [(URL_PAGINA[destino], destino) for _, _, destino in PASOS]                               # hacia Auditoría de cámaras, Cola de revisión y Ética y límites
    assert [d for _, _, d in PASOS] == ["Auditoría de cámaras", "Cola de revisión", "Ética y límites"] and all((R / "app" / ARCHIVO_PAGINA[d]).exists() for _, _, d in PASOS)
    assert [p.proto.label for p in _abrir(entorno, monkeypatch, "Ética y límites").get("page_link")] == ["Ver Validación"]


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_las_cifras_de_etica_son_las_de_validacion_y_del_resumen(monkeypatch: pytest.MonkeyPatch) -> None:
    from waymo_evaluacion.ep3 import formato as F
    from waymo_evaluacion.ep3.app_logica import cargar_datos, datos_ciclistas

    at = _abrir_real(monkeypatch, "Ética y límites")
    etica = _visible(at)
    ir_a(at, "Validación")
    val = _visible(at)
    D = cargar_datos(R / "data/09_app_ep3")
    c = datos_ciclistas(D["evidencia"]["posthoc__equidad"])
    claves = {t["titulo"]: t["valor"] for t in D["kpis"]["tarjetas"]}
    for esperado in (claves["AUC fuera de fold"], claves["Recall en el punto A"], claves["Captura al revisar el 20 %"], F.porcentaje(c["peaton"]), F.porcentaje(c["ciclista"])):
        assert esperado.replace("\xa0", " ") in etica, esperado                                                # la ficha lleva las cifras de las tarjetas de kpis
    for esperado in (claves["AUC fuera de fold"], F.porcentaje(c["peaton"]), F.porcentaje(c["ciclista"])):
        assert esperado.replace("\xa0", " ") in val, esperado                                                  # y Validación, las mismas
    assert f"{F.entero(c['positivos'])} casos en {F.entero(c['segmentos'])} segmentos" in etica
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    cuerpo = fuente[fuente.index("def etica("):fuente.index("def ayuda(")]
    assert not re.search(r"0,823|79,8|61,9|80,6|44,3|\b115\b|\b14 segmentos|41 segmentos", cuerpo)           # ninguna cifra escrita a mano


# ------------------------------------------------------------------------------------------------------------ accesibilidad
def test_los_iconos_son_decorativos_y_la_barra_tiene_descripcion_y_numeros(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    import estilos as E

    html = E.hero_decide("t", "x", ("a", "b")) + E.tarjeta_icono("T", "<p>x</p>", "datos") + E.barra_comparacion([("Peatones", 0.8, "80,6 %", False), ("Ciclistas", 0.44, "44,3 %", True)], "Casos encontrados: peatones 80,6 %, ciclistas 44,3 %.")
    html = html.replace(" ", " ")
    assert html.count('aria-hidden="true"') >= 5 and 'role="img" aria-label="Casos encontrados' in html and "80,6 %" in html and "44,3 %" in html
    css = E.css()
    bloque = css[css.index("F36: Ética y límites"):css.index("F35: Puntuar datos nuevos")]
    tamanos = [float(x) for x in re.findall(r"font-size: ([\d.]+)rem", bloque)]
    assert tamanos and min(tamanos) >= 0.75 and not re.search(r"#[0-9A-Fa-f]{6}", bloque) and "999px" not in bloque and "font-weight: 700" not in bloque and "linear-gradient" not in bloque
    at = _abrir(entorno, monkeypatch, "Ética y límites")
    h = " ".join(m.value for m in at.markdown)
    assert 'class="aud-hero"' in h and h.index("Decide siempre una persona.") < h.index("Propósito") and "Nunca debe usarse para descartar cajas sin revisarlas." in h
    assert h.count("Ordenar las cajas 3D de peatones y ciclistas") == 1 and h.count("nunca debe usarse para descartar") == 0                          # las frases de regla de uso no se duplican en Propósito
