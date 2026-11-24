"""F26: marca propia (Lente), afirmación del Resumen, pie con la atribución, textos según el entorno (EP3_ENTORNO), reordenamiento del Resumen y puntaje dentro de «Cómo se calcula».
Escribe solo en ``tmp_path``."""
from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

import pytest

from tests.ep3.test_app import textos
from tests.ep3.test_pagina_f24 import _abrir, _sin_css, entorno  # noqa: F401  (``entorno`` es la fixture del módulo de F24)

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))


# ------------------------------------------------------------------------------------------------------------ A3 y constantes
def test_la_identidad_vive_en_constantes_y_el_nombre_antiguo_no_esta_en_la_pagina() -> None:
    from waymo_evaluacion.ep3 import app_logica as A

    assert A.NOMBRE_PRODUCTO == "Lente" and A.PRODUCTO == A.NOMBRE_PRODUCTO and A.SUBLINEA_MARCA == "Waymo Open Dataset v2" and A.TITULO_RESUMEN == "Estado de las cámaras"
    assert A.SUBTITULO_RESUMEN == "Etiquetas 2D de peatones y ciclistas en {n} segmentos."          # F28: sin «de desarrollo»
    assert A.ATRIBUCION_WAYMO.startswith("This application was made using the Waymo Open Dataset, provided by Waymo LLC") and A.ATRIBUCION_WAYMO.endswith("(see waymo.com/open/terms).")
    assert A.SECCIONES[0] == "Resumen"                                                                                   # la etiqueta del menú no cambia
    for p in sorted((R / "app").rglob("*.py")) + [R / "src/waymo_evaluacion/ep3/app_logica.py"]:
        assert "Auditor de etiquetas" not in p.read_text(encoding="utf-8"), p.name
    fuente = (R / "app" / "app.py").read_text(encoding="utf-8")
    assert "page_title=NOMBRE_PRODUCTO" in fuente and "E.wordmark(NOMBRE_PRODUCTO, SUBLINEA_MARCA)" in fuente and "E.pie(ATRIBUCION_WAYMO, _version, _segmentos)" in fuente


def test_el_simbolo_es_propio_se_dibuja_con_cinco_cunas_y_el_favicon_es_el_mismo() -> None:
    import estilos as E
    from PIL import Image

    w = E.wordmark("Lente", "Waymo Open Dataset v2")
    assert w.startswith("<svg") and "http" not in w.replace(E.SVG_NS, "") and "<image" not in w and "<use" not in w
    assert w.count("<polygon") == 5 and ">Lente<" in w and ">Waymo Open Dataset v2<" in w and 'font-size="14" font-weight="600"' in w and 'font-size="11"' in w
    assert E.TOKENS["acento"] in w and E.TOKENS["panel_alto"] in w and E.TOKENS["panel_alto_borde"] in w and E.TOKENS["texto_2"] in w          # símbolo en panel alto con borde y cuñas en acento
    assert "Solución v3" not in w                                                                                         # la versión pasó al pie
    assert E.simbolo_svg(16).startswith('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"')
    sys.path.insert(0, str(R / "scripts" / "ep3"))
    import generar_icono as G

    icono = Image.open(R / "app/assets/icono.png").convert("RGBA")
    assert icono.size == (256, 256)
    nuevo = G.dibujar(256)
    assert list(icono.getdata()) == list(nuevo.getdata()), "app/assets/icono.png no es el que genera scripts/ep3/generar_icono.py"
    assert (R / "images/ep3/pagina/f26_favicon_16.png").exists()


# ------------------------------------------------------------------------------------------------------------ A1, A4: título y afirmación
def test_el_resumen_tiene_el_titulo_nuevo_y_el_menu_sigue_diciendo_resumen(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    from waymo_evaluacion.ep3.app_logica import SECCIONES

    at = _abrir(entorno, monkeypatch, "Resumen")
    assert at.title[0].value == "Estado de las cámaras" and SECCIONES[0] == "Resumen"
    t = _sin_css(textos(at))
    assert "Etiquetas 2D de peatones y ciclistas en 3 segmentos." in t and "Estado de las etiquetas 2D" not in t


# ------------------------------------------------------------------------------------------------------------ A2, A5: sin chip y con pie
def test_el_pie_lleva_la_atribucion_y_la_version_en_dos_lineas_en_todas_las_vistas(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    import estilos as E
    from waymo_evaluacion.ep3.app_logica import ATRIBUCION_WAYMO, SECCIONES

    pie = E.pie(ATRIBUCION_WAYMO, "Solución v3 congelada el 2026-11-14", 41)
    assert pie == f'<div class="aud-pie"><p>{ATRIBUCION_WAYMO}</p><p>Solución v3 congelada el 2026-11-14. Datos de desarrollo, 41 segmentos.</p></div>'
    css = E.css()
    regla = re.search(r"\.aud-pie p \{[^}]*\}", css).group(0)
    assert "font-size: .8rem" in regla and "color: var(--texto-3)" in regla and "aviso" not in regla and "aviso" not in re.search(r"\.aud-pie \{[^}]*\}", css).group(0)      # 12 px en Texto 3, sin ámbar
    at = _abrir(entorno, monkeypatch, "Resumen")
    for s in SECCIONES:
        from tests.ep3.test_app import ir_a

        ir_a(at, s)
        t = textos(at)
        assert ATRIBUCION_WAYMO in t and "Datos de desarrollo, " in t, s
        assert "Waymo Open Dataset v2, uso académico" not in t, s


# ------------------------------------------------------------------------------------------------------------ B1: entorno
def test_sin_la_variable_los_textos_son_los_de_siempre_y_con_servidor_son_la_variante(monkeypatch: pytest.MonkeyPatch) -> None:
    from waymo_evaluacion.ep3.app_logica import TEXTOS_ENTORNO, entorno_pagina, preguntas_frecuentes, texto_entorno

    monkeypatch.delenv("EP3_ENTORNO", raising=False)
    assert entorno_pagina() == "local" and texto_entorno("donde_corre") == "Solo en este equipo (localhost), sin conexión a internet. No debe exponerse en una red sin autenticación."
    assert texto_entorno("puntuar_subtitulo").endswith("su cola de cajas.") and texto_entorno("puntuar_etiqueta") == "Procesamiento local y en memoria"
    assert texto_entorno("consideracion_etica").endswith("Nada se guarda ni se envía.")
    assert dict(preguntas_frecuentes())["¿Se guardan o se envían los archivos?"].startswith("No. Nada se guarda ni se envía")
    for valor in ("otro", "", "local"):
        monkeypatch.setenv("EP3_ENTORNO", valor)
        assert entorno_pagina() == "local", valor
    for valor in (" Servidor ", "publicado", "PUBLICADO"):                                                                    # F36: «servidor» sigue valiendo como alias de «publicado»
        monkeypatch.setenv("EP3_ENTORNO", valor)
        assert entorno_pagina() == "publicado", valor
    assert texto_entorno("donde_corre").startswith("En un servidor conectado a internet ([nombre del servicio]). Cualquiera que tenga el enlace puede abrir la aplicación.")
    assert "se procesan en la memoria del servidor durante la sesión y no se guardan" in texto_entorno("consideracion_etica")
    assert dict(preguntas_frecuentes())["¿Se guardan o se envían los archivos?"].startswith("Los archivos que se suben se procesan en la memoria del servidor durante la sesión y no se guardan")
    assert texto_entorno("borrador") == "borrador: verificar"
    assert set(TEXTOS_ENTORNO["local"]) == set(TEXTOS_ENTORNO["publicado"])
    for clave in TEXTOS_ENTORNO["publicado"]:
        t = TEXTOS_ENTORNO["publicado"][clave]
        assert "localhost" not in t and "Nada se guarda ni se envía" not in t and "en este equipo" not in t.lower(), clave                 # ninguna afirmación local sobrevive en la variante publicada


@pytest.mark.parametrize("valor, locales", [(None, True), ("publicado", False)])
def test_las_paginas_usan_la_variante_del_entorno(entorno: Path, monkeypatch: pytest.MonkeyPatch, valor: str | None, locales: bool) -> None:   # noqa: F811
    if valor is None:
        monkeypatch.delenv("EP3_ENTORNO", raising=False)
    else:
        monkeypatch.setenv("EP3_ENTORNO", valor)
    etica = textos(_abrir(entorno, monkeypatch, "Ética y límites"))
    puntuar = textos(_abrir(entorno, monkeypatch, "Puntuar datos nuevos"))
    ayuda = textos(_abrir(entorno, monkeypatch, "Ayuda y glosario"))
    assert ("Solo en este equipo (localhost)" in etica) is locales and ("Nada se guarda ni se envía" in etica) is locales
    assert ("En un servidor conectado a internet" in etica) is not locales and ("se procesan en la memoria del servidor durante la sesión" in etica) is not locales
    assert ("Procesamiento local y en memoria" in puntuar) is locales and ("Procesamiento en el servidor y en memoria" in puntuar) is not locales
    assert ("No. Nada se guarda ni se envía" in ayuda) is locales and ("Los archivos que se suben se procesan en la memoria del servidor durante la sesión y no se guardan" in ayuda) is not locales


def test_los_archivos_cargados_no_se_escriben_a_disco() -> None:
    """Respaldo de la afirmación «no se guardan» de la variante de servidor: la página lee el archivo con ``pd.read_parquet`` (en memoria) y no escribe nada del usuario."""
    from waymo_evaluacion.ep3.inferencia import puntuar_segmento

    for fn in (puntuar_segmento,):
        codigo = inspect.getsource(fn)
        assert not re.search(r"write_|\.to_parquet\(|\.to_csv\(|open\(|tempfile|\.save\(|joblib\.dump|shutil", codigo), fn.__name__
    for p in sorted((R / "app").rglob("*.py")):
        t = p.read_text(encoding="utf-8")
        assert not re.search(r"\.guardar\(|write_bytes|write_text|tempfile|joblib\.dump|shutil\.copy|\.to_parquet\(", t.replace("sin write_text", "")), p.name
        assert "open(" not in re.sub(r"[^\n]*(subprocess|webbrowser)[^\n]*", "", t) or p.name in ("lanzar.py",), p.name
    for p in (R / "src/waymo_evaluacion/ep3/puntuar.py", R / "src/waymo_evaluacion/ep3/tablas_estandar.py"):                                    # F35: la lógica de Puntuar vive en un módulo que tampoco escribe a disco
        t = p.read_text(encoding="utf-8")
        assert not re.search(r"\.guardar\(|write_bytes|write_text|tempfile|joblib\.dump|shutil|\.to_parquet\(|[^.]open\(", t), p.name
    puntuar = (R / "src/waymo_evaluacion/ep3/puntuar.py").read_text(encoding="utf-8")
    assert "pd.read_parquet(io.BytesIO(" in puntuar and ".to_csv(index=False)" in puntuar and "zipfile.ZipFile(buf" in puntuar                  # se lee y se arma en memoria (bytes), no en un archivo


# ------------------------------------------------------------------------------------------------------------ B2: líneas huérfanas
def test_titulos_y_frases_se_equilibran_y_los_parrafos_evitan_la_palabra_suelta() -> None:
    import estilos as E

    css = E.css()
    assert re.search(r"h1, h2, h3, h4\) , \.aud-descripcion, \.aud-resultado[^{]*\{ text-wrap: balance; \}", css)
    assert "text-wrap: pretty" in css and re.search(r"\.aud-titular \{[^}]*text-wrap: balance", css)
    assert not re.search(r"\.aud-descripcion \{[^}]*max-width", css)                                                       # el subtítulo usa todo el ancho: ya no hay un tope que lo corte a ~560 px


# ------------------------------------------------------------------------------------------------------------ B4: puntaje
def test_el_puntaje_interno_vive_dentro_de_como_se_calcula() -> None:
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    cuerpo = fuente[fuente.index("def explica("):fuente.index("# ---", fuente.index("def explica("))]
    assert cuerpo.count("F.entero(s)") == 1 and cuerpo.count("E.pasos_calculo(") == 1                                    # F33: el puntaje solo aparece en el paso 2 de «Cómo se calcula»
    bloque = cuerpo[cuerpo.index('key="ex_pasos"'):cuerpo.index('key="ex_curva"')]
    assert "Cómo se calcula" in bloque and "F.entero(s)" in bloque and "EXP_PASOS" in bloque


# ------------------------------------------------------------------------------------------------------------ C1: porcentajes
def test_los_casos_encontrados_por_clase_se_muestran_como_porcentaje() -> None:
    import secciones as S

    ctx = {"K": {"tarjetas": []}, "ciclistas": {"ciclista": 0.4435, "peaton": 0.806, "positivos": 115.0, "segmentos": 14.0}}
    filas = {f[0]: f[1] for f in S._cifras_de_apoyo(ctx, {"cajas": 10, "prevalencia": 0.2})}
    assert filas["Casos encontrados en peatones"].replace("\xa0", " ") == "80,6 %" and filas["Casos encontrados en ciclistas"].replace("\xa0", " ") == "44,4 %"
    assert "0,44" not in " ".join(str(v) for f in filas.values() for v in (f,))                                  # F29: sin la alerta del Resumen, las cifras de apoyo son las únicas del Resumen/Validación
