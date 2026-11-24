"""F24 (DEC-97 a DEC-105): cambio de piel a un tema oscuro tipo consola de control y defectos concretos de maquetación. La estructura y el contenido son los de F23.
Cubre: los tokens como única fuente de verdad, el tema nativo generado desde ellos, una sola familia sans, las reglas de CSS pedidas, las vistas que cambiaron y los archivos de verificación
(medición del Resumen en modo normal y presentación, contraste real, paleta, 404, sello)."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

from tests.ep3.test_app import _datos_sinteticos, _modelos_sinteticos, ir_a, textos

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))

# la tabla de tokens del prompt de F24
TOKENS_PEDIDOS = {"fondo": "#0B1220", "barra": "#0E1729", "barra_borde": "#1E2B45", "panel": "#121C30", "panel_borde": "#22314D", "panel_alto": "#18253D", "panel_alto_borde": "#2A3A57",
                  "texto": "#E8EEF8", "texto_2": "#A9B8CF", "texto_3": "#8696B0", "acento": "#6FA0FF", "sano": "#3CC9B8", "sano_relleno": "#14535A", "hueco": "#FF7A6B", "hueco_fondo": "#3A1A22",
                  "sin_datos": "#1B2740", "sin_datos_borde": "#3A4B6B", "aviso_texto": "#F5B73B"}                      # F25: el ámbar quedó solo como color del punto de advertencia; sus fondo y borde se quitaron


@pytest.fixture(scope="module")
def entorno(tmp_path_factory):
    base = tmp_path_factory.mktemp("f24")
    _datos_sinteticos(base / "datos")
    _modelos_sinteticos(base / "modelos")
    (base / "datos" / "evidencia" / "ie12__brazo_C_y_equilibrio.csv").write_text("candidato,Fraccion_80_C,Fraccion_80_A\nRegla top,0.3,0.45\n", encoding="utf-8")
    return base


def _abrir(entorno: Path, monkeypatch: pytest.MonkeyPatch, seccion: str | None = None):
    at_mod = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.setenv("WAYMO_APP_DATA", str(entorno / "datos"))
    monkeypatch.setenv("WAYMO_APP_MODELOS", str(entorno / "modelos"))
    at = at_mod.AppTest.from_file(str(R / "app" / "app.py"), default_timeout=90).run()
    if seccion:
        ir_a(at, seccion)
    assert not at.exception, at.exception
    return at


def _sin_css(t: str) -> str:
    return re.sub(r"<style>.*?</style>", "", t, flags=re.S)


# ------------------------------------------------------------------------------------------------------------ tokens: una sola fuente de verdad
def test_los_tokens_son_los_del_prompt_y_pasan_el_contraste_medido() -> None:
    import estilos as E

    for k, v in TOKENS_PEDIDOS.items():
        assert E.TOKENS[k].upper() == v, k
    for fg, bg in E.PARES_CONTRASTE:
        assert E.contraste(E.TOKENS[fg], E.TOKENS[bg]) >= 4.5, (fg, bg)
    c = lambda a, b: E.contraste(E.TOKENS[a], E.TOKENS[b])                                                           # noqa: E731
    # las cifras del prompt (sobre el panel): texto 14,6; texto 2 8,5; texto 3 5,7 (5,1 sobre el panel alto); acento 6,6; sano 8,3; hueco 6,7
    assert round(c("texto", "panel"), 1) == 14.6 and round(c("texto_2", "panel"), 1) == 8.5 and round(c("texto_3", "panel"), 1) == 5.7 and round(c("texto_3", "panel_alto"), 1) == 5.1
    assert round(c("acento", "panel"), 1) == 6.6 and round(c("sano", "panel"), 1) == 8.3 and round(c("hueco", "panel"), 1) == 6.7
    assert c("fondo", "acento") >= 4.5                                                                               # el texto del botón primario (#0B1220 sobre el acento)


def test_no_hay_colores_sueltos_fuera_de_estilos() -> None:
    archivos = [p for p in (R / "app").rglob("*.py") if p.name != "estilos.py" and "__pycache__" not in p.parts]
    assert archivos
    for p in archivos:
        assert not re.search(r"#[0-9A-Fa-f]{6}\b", p.read_text(encoding="utf-8")), p.relative_to(R)                  # los hex salen de TOKENS
    import estilos as E

    fuera = [l for l in (R / "app" / "estilos.py").read_text(encoding="utf-8").split("\n") if re.search(r"#[0-9A-Fa-f]{6}\b", l) and not l.startswith(('    "', "RAMPA", "CURVAS", "SERIE", "FLUJOS"))]
    assert not fuera, fuera                                                                                          # ni siquiera dentro del CSS: solo la tabla de tokens y las paletas validadas
    assert E.RAMPA_SANA[-1] == E.TOKENS["sano"] and E.SERIE_GRIS == E.TOKENS["texto_3"]


def _generador_de_config():
    spec = importlib.util.spec_from_file_location("generar_config_tema", R / "scripts/ep3/generar_config_tema.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_los_dos_config_toml_salen_de_los_tokens_y_conservan_la_seguridad() -> None:
    import estilos as E

    g = _generador_de_config()
    for ruta in g.ARCHIVOS:
        t = ruta.read_text(encoding="utf-8")
        assert g.generar(t) == t, ruta.name                                                                          # lo escrito es exactamente lo que generan los tokens
        assert E.tema_toml() in t and 'base = "dark"' in t
    raiz = (R / ".streamlit/config.toml").read_text(encoding="utf-8")
    assert 'address = "localhost"' in raiz and "headless" in raiz and "gatherUsageStats = false" in raiz and 'toolbarMode = "minimal"' in raiz     # las claves de seguridad siguen
    assert "gatherUsageStats = false" in (R / "app/.streamlit/config.toml").read_text(encoding="utf-8")
    t = E.tema_toml()
    for clave in ("baseRadius", "borderColor", "linkColor", "linkUnderline = true", "dataframeHeaderBackgroundColor", "showSidebarBorder = true"):
        assert clave in t


def test_inter_es_opcional_y_si_esta_en_el_repo_se_carga_sin_internet(tmp_path: Path) -> None:
    import estilos as E

    sin = E.tema_toml(tmp_path / "no_existe.woff2")
    assert 'font = "sans serif"' in sin and "fontFaces" not in sin                                                    # sin el archivo, la pila de sistema y sin fallar
    archivo = tmp_path / "Inter-Variable.woff2"
    archivo.write_bytes(b"wOF2")
    con = E.tema_toml(archivo)
    assert 'font = "Inter"' in con and "[[theme.fontFaces]]" in con and 'url = "app/static/fonts/Inter-Variable.woff2"' in con and "http" not in con
    assert E.PILA_TIPOGRAFICA.startswith('"Inter"')
    assert not E.ARCHIVO_INTER.exists() or (E.ARCHIVO_INTER.parent / "LICENSE.txt").exists() or (E.ARCHIVO_INTER.parent / "OFL.txt").exists()        # si el usuario deja la fuente, debe traer su licencia OFL


# ------------------------------------------------------------------------------------------------------------ reglas de CSS pedidas
def test_el_css_cumple_las_reglas_globales_del_prompt() -> None:
    import estilos as E

    css = E.css()
    assert "[data-testid=\"stTabs\"] [data-baseweb=\"tab-highlight\"] { height: 2px; background: var(--acento); }" in css and 'button[role="tab"][aria-selected="true"] { color: var(--acento); font-weight: 600; }' in css     # 2: pestañas
    assert re.search(r"stCaptionContainer\"\], \[data-testid=\"stCaptionContainer\"\] \* , \.stCaption \{ color: var\(--texto-3\) !important; opacity: 1 !important; \}", css)                          # 3: notas sin opacidad
    assert "opacity: .6" not in css and "opacity:.6" not in css
    assert "input::placeholder { color: var(--texto) !important; opacity: 1 !important;" in css and "background: var(--panel-alto); border-color: var(--panel-alto-borde); color: var(--texto); }" in css            # 9: filtros activos
    assert "stBaseButton-primary" in css and "background: var(--acento)" in css and "color: var(--fondo)" in css                                                                                              # 18: botón primario
    assert "border: 1.5px dashed var(--sin-datos-borde)" in css                                                                                                                                              # 18: zonas de carga punteadas
    assert "height: 10px; border-radius: 5px" in css                                                                                                                                                         # 7: barras de 10 px
    assert re.search(r"\.aud-nota \{[^}]*border-left: 2px solid var\(--sin-datos-borde\)", css) and "color: var(--texto-2)" in css                                                                               # 11: nota del empate
    assert "stSliderThumbValue" in css and "stSlider\"] [data-baseweb=\"slider\"]" in css                                                                                                                    # 12: controles
    assert "padding: 1rem 1.4rem 1rem 1.4rem" in css                                                                                                                                                       # 5: 24 px de relleno inferior
    assert "[data-testid=\"stDataFrame\"] { border: 1px solid var(--panel-borde)" in css                                                                                                                     # el st.dataframe solo recibe el tema y el borde


def test_las_barras_son_mas_altas() -> None:
    import estilos as E

    h = E.tabla_cifras([("a", "1", "", 0.5, E.TOKENS["acento"])])
    assert 'class="aud-barra"' in h and 'style="width:50.0%;background:#6FA0FF"' in h                                                                           # 7


def test_el_detalle_de_la_cola_pone_el_anillo_sobre_la_cifra_grande(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    at.session_state["tabla_cola"] = {"selection": {"rows": [0], "columns": [], "cells": []}}
    at.run()
    assert not at.exception
    detalle = next(m.value for m in at.markdown if 'class="aud-detalle-cabeza"' in m.value)
    assert detalle.index('class="aud-anillo"') < detalle.index('class="aud-probabilidad"') and 'width="96"' in detalle                                        # 10 (F32): anillo de ~96 px sobre la cifra
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert 'st.columns([2.15, 1], gap="medium")' in fuente and "E.anillo_camaras" in fuente
    import estilos as E

    css = E.css()
    assert "padding: 20px 20px 24px 20px" in css and "flex-direction: column" in css                                                                           # 10: 20 px de relleno y 24 px abajo


def test_el_mapa_no_se_desplaza_por_dentro_y_la_leyenda_cabe_en_una_linea() -> None:
    import estilos as E

    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert "alto_fila * max(n_seg, 1)" in fuente and 'st.container(key="mapa_calor")' in fuente and "height=560" not in fuente                                  # 14: sin desplazamiento interno (F31: solo se dibujan las filas visibles)
    ley = E.leyenda_mapa(100)
    lineas = re.findall(r'<span class="aud-ley"[^>]*>(.*?)</span>(?=<span class="aud-ley"|</div>)', ley, flags=re.S)
    textos_cortos = [re.sub(r"<[^>]+>", "", l) for l in lineas]
    assert len(textos_cortos) == 3 and all(len(x) <= 72 for x in textos_cortos), textos_cortos                                                                  # F31: tres estados en una línea (escala, hueco, sin datos)
    assert "title=" in ley and "no es lo mismo que 0 %" in ley                                                                                                   # la explicación larga queda en el tooltip
    assert E.RAMPA_SANA[0] in ley or "escala" in ley


def test_la_tabla_de_criterios_usa_icono_y_texto_sin_rojo_ni_ambar() -> None:
    import estilos as E

    h = E.tabla_criterios(["Candidato", "O1"], [["Regla", "Cumple"], ["LR", "No cumple"]], elegida=0, columnas_cumple=(1,))
    assert h.count("<svg") == 2 and "M3 8.5 L6.5 12 L13 4.5" in h and "M4 4 L12 12 M12 4 L4 12" in h and ">Cumple<" in h and ">No cumple<" in h and 'class="elegida"' in h and "Elegida" in h   # 17
    css = E.css()
    assert re.search(r"\.cumple \{ color: var\(--sano\)", css) and re.search(r"\.no-cumple \{ color: var\(--texto\)", css)                                   # «✓ Cumple» en Sana y «✕ No cumple» en Texto
    assert "tr.elegida td { background: var(--panel-alto); }" in css
    seccion = css[css.index(".aud-tabla.criterios .cumple"):css.index(".aud-criterios-def")]
    assert "--hueco" not in seccion and "--aviso" not in seccion                                                      # el rojo y el ámbar están reservados
    assert not re.search("[✓✕✔✖]", (R / "app" / "estilos.py").read_text(encoding="utf-8"))        # los iconos son SVG propios, no caracteres (la prueba de emojis sigue en pie)


def test_las_series_de_validacion_usan_la_paleta_oscura() -> None:
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert "range=[E.FLUJOS_COLORES[b] for b in brazos]" in fuente and "columns=3" in fuente                                                      # 16: tres series y leyenda en una fila
    assert 'color=E.TOKENS["texto"])' in fuente and 'text="Etiqueta:N"' in fuente and 'x=alt.X("Candidato:N"' in fuente                                                                  # valores en Texto (F34: con el nombre corto del flujo debajo)
    assert 'configure(background="transparent"' in fuente and 'gridColor=t["panel_borde"]' in fuente and 'labelColor=t["texto_2"]' in fuente and "labelFontSize=12" in fuente


def test_puntuar_tiene_el_ejemplo_como_boton_discreto_y_subir_el_archivo_como_accion_principal(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """F35 reemplaza a F24: el ejemplo pasa a ser un botón secundario («¿Solo desea ver cómo funciona?») y la acción principal es «Elegir archivo» del archivo 1 (botón destacado por CSS)."""
    import estilos as E

    at = _abrir(entorno, monkeypatch, "Puntuar datos nuevos")
    boton = next(b for b in at.button if b.label == "Usar un segmento de desarrollo de ejemplo")
    assert boton.proto.type == "secondary"
    assert [b.label for b in at.button if b.proto.type == "primary"] == ["Puntuar segmento"]                                    # F39: la acción principal es el botón «Puntuar segmento»
    assert ".st-key-pt_up1 [data-testid=\"stFileUploaderDropzone\"] button { background: var(--acento)" not in E.css()          # F39: los dos cargadores tienen el mismo estilo (ya no se destaca el del archivo 1)


def test_las_curvas_de_referencia_llevan_etiqueta_directa() -> None:
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert 'n.endswith("(referencia)")' in fuente and "mark_point(shape=\"diamond\"" in fuente and "*capas_et" in fuente and 'color=E.TOKENS["texto_2"]).encode(x="presupuesto:Q", y="recall:Q", text="t:N")' in fuente   # el nombre va en texto neutro, no en el color de la serie


def test_correcciones_de_la_revision_de_capturas_de_f24() -> None:
    """Lo que se vio al revisar las capturas una por una y se corrigió: líneas continuas en la lista de cámaras, «segmento × cámara» sin partirse, notas y leyenda coherentes con la piel oscura."""
    import estilos as E

    css = E.css()
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    from waymo_evaluacion.ep3 import validacion as V

    assert "Línea negra" not in fuente and V.LEYENDA_INTERVALO == "Línea clara: intervalo de confianza 95 % por segmentos." and fuente.count("V.LEYENDA_INTERVALO") == 2     # el intervalo se dibuja claro sobre fondo oscuro (F34: el texto vive en validacion.py)
    assert "Cajas con par 2D: 0 %" in E.leyenda_mapa(100) and "100 %" in E.leyenda_mapa(100)                                                    # la leyenda no queda cortada


def test_las_capturas_de_la_pestana_de_curvas_existen() -> None:
    carpeta = R / "images/ep3/pagina"
    faltan = [n for n in ("02b_curvas_sin_referencia.png", "02b_curvas_con_xgboost.png", "02b_curvas_con_e2.png") if not (carpeta / n).exists()]
    if faltan:
        pytest.skip(f"todavía no se capturaron las curvas (scripts/ep3/f24_capturar_curvas.py): {faltan}")
    assert all((carpeta / n).stat().st_size > 20_000 for n in ("02b_curvas_sin_referencia.png", "02b_curvas_con_xgboost.png", "02b_curvas_con_e2.png"))


# ------------------------------------------------------------------------------------------------------------ verificación registrada
def test_el_resumen_cabe_en_640_px() -> None:
    """F29: la primera pantalla (1366 x 768) muestra los indicadores, el titular y la lista de alertas; la última fila de alerta termina en 640 px o antes."""
    res = R / "docs/ep3/f24_fold_resumen.json"
    if not res.exists():
        pytest.skip("todavía no se midió el Resumen (scripts/ep3/f24_medir_resumen.py)")
    m = json.loads(res.read_text(encoding="utf-8"))
    assert set(m) == {"normal"}                                                                                                                                  # F30: ya no hay modo presentación
    for modo, v in m.items():
        assert v["viewport"] == [1366, 768] and v["limite_px"] == 640, modo
        assert v["panel_dentro_del_limite"] and v["panel_termina_en_px"] <= 640, (modo, v["panel_termina_en_px"])                                                  # la lista de alertas dentro de 640 px
        assert v["indicadores_visibles"] and v["titular_visible"] and v["lista_de_alertas_visible"] and v["scroll_horizontal_px"] <= 0, modo
        assert len(v["filas_de_alerta"]) == 2, modo                                                                                                                 # con los datos actuales: 2 alertas


def test_el_contraste_real_de_la_pagina_esta_medido_y_no_hay_texto_bajo_4_5() -> None:
    res = R / "docs/ep3/f24_contraste.json"
    if not res.exists():
        pytest.skip("todavía no se midió el contraste real (scripts/ep3/f24_auditar_contraste.py)")
    d = json.loads(res.read_text(encoding="utf-8"))
    s = d["resumen"]
    assert s["vistas"] >= 14 and s["textos_medidos"] > 800 and s["textos_por_debajo"] == 0 and s["razon_minima_dom"] >= 4.5                                          # sobre el DOM
    assert s["notas_muestreadas"] >= 20 and s["razon_minima_en_pixeles"] >= 4.5                                                                                  # y sobre los píxeles de las notas pequeñas
    assert all(m["opacidad_css"] == "1" for m in d["notas_en_pixeles"])                                                                                          # 3: ninguna nota con opacidad


def test_las_capturas_registran_los_404_con_su_url_y_no_hay_errores_de_consola() -> None:
    res = R / "data/08_reporting_ep3/capturas_resultado.json"
    if not res.exists():
        pytest.skip("todavía no se generaron las capturas")
    r = json.loads(res.read_text(encoding="utf-8"))
    assert all("404_urls" in x for x in r) and all(not x["errores_consola"] for x in r)
    assert all(not x["404_urls"] or all(u.startswith("http://localhost") for u in x["404_urls"]) for x in r)           # los 404 son de la propia página local (rutas internas de Streamlit)
    assert max(x["geometria"]["scroll_horizontal_px"] for x in r if x.get("geometria")) <= 0


def test_el_sello_sigue_intacto() -> None:
    res = R / "docs/ep3/f24_sello_despues.json"
    if not res.exists():
        pytest.skip("todavía no se comprobó el sello (scripts/ep3/f23_integridad_sello.py --comprobar --etiqueta f24)")
    d = json.loads(res.read_text(encoding="utf-8"))
    assert d["intacto"] and not d["cambiados"] and not d["faltan"] and not d["nuevos"] and not d["git_status_sobre_lo_sellado"] and d["archivos_comparados"] >= 100


def test_el_reporte_de_f24_tiene_las_tres_secciones() -> None:
    ruta = R / "docs/ep3/REPORTE_F24.md"
    if not ruta.exists():
        pytest.skip("todavía no se generó el reporte")
    t = ruta.read_text(encoding="utf-8")
    for titulo in ("## Qué se hizo", "## Qué no se pudo y por qué", "## Archivos modificados"):
        assert titulo in t, titulo
