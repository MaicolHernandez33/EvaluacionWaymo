"""F23 (DEC-87 a DEC-95): rediseño estructural de la página. El anillo de cámaras manda en el Resumen, la Cola trae seis columnas y un panel siempre visible, la Auditoría muestra «sin datos» en gris plano,
la barra lateral es clara, Puntuar pone primero las acciones, «Selección» trae criterios con nombre y la paleta de curvas pasó la validación de dataviz.
Solo presentación: las cifras y los textos sellados no cambian (los cubren las pruebas de F20 y F21)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

from tests.ep3.test_app import _datos_sinteticos, _modelos_sinteticos, ir_a, textos
from tests.ep3.test_pagina_f20 import HAY_REAL, _abrir_real
from waymo_evaluacion.ep3 import formato as F
from waymo_evaluacion.ep3.app_logica import CAMARAS, cargar_datos, criterios_seleccion, estado_camaras_segmento, inicio_resumen, matriz_calor

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))


@pytest.fixture(scope="module")
def entorno(tmp_path_factory):
    base = tmp_path_factory.mktemp("f23")
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


# ------------------------------------------------------------------------------------------------------------ sistema visual
def test_la_barra_lateral_es_un_tono_sobre_el_lienzo_con_una_linea_derecha() -> None:
    import estilos as E

    css = E.css()
    assert E.TOKENS["barra"] != E.TOKENS["fondo"] and E.contraste(E.TOKENS["barra"], E.TOKENS["fondo"]) < 1.2         # un tono sobre el lienzo, no un bloque distinto
    assert re.search(r'\[data-testid="stSidebar"\] \{ background: var\(--barra\); border-right: 1px solid var\(--barra-borde\);', css)      # con una línea derecha
    for ruta in (R / ".streamlit/config.toml", R / "app/.streamlit/config.toml"):
        t = ruta.read_text(encoding="utf-8")
        lateral = t.split("[theme.sidebar]")[1]
        assert f'backgroundColor = "{E.TOKENS["barra"]}"' in lateral and f'textColor = "{E.TOKENS["texto"]}"' in lateral and f'borderColor = "{E.TOKENS["barra_borde"]}"' in lateral, ruta.name
        assert 'base = "dark"' in t and "showSidebarBorder = true" in t


def test_contraste_de_texto_item_activo_y_wordmark() -> None:
    import estilos as E

    for fg, bg in E.PARES_CONTRASTE:
        assert E.contraste(E.TOKENS[fg], E.TOKENS[bg]) >= 4.5, (fg, bg)
    assert E.contraste(E.TOKENS["acento"], E.TOKENS["acento_fondo"]) >= 4.5                                          # ítem activo de la barra: acento sobre su tinte
    assert E.contraste(E.TOKENS["texto_3"], E.TOKENS["panel_alto"]) >= 4.5                                           # las notas, el mínimo permitido, también sobre el panel alto
    w = E.wordmark("Lente", "Waymo Open Dataset v2")
    assert E.TOKENS["texto"] in w and E.TOKENS["texto_2"] in w and "Lente" in w and "Waymo Open Dataset v2" in w and "Solución v3" not in w and "·" not in w and "http" not in w.replace(E.SVG_NS, "")


def test_una_sola_familia_sans_sin_descargar_nada() -> None:
    import estilos as E

    css = E.css()
    assert E.PILA_TIPOGRAFICA.startswith('"Inter"') and "Segoe UI" in E.PILA_TIPOGRAFICA and E.PILA_TIPOGRAFICA.endswith("sans-serif")      # una sola familia sans para todo
    fuente = (R / "app" / "estilos.py").read_text(encoding="utf-8")
    assert "Cambria" not in fuente and "--display" not in css and "serif" not in css.replace("sans-serif", "")                       # sin serif ni segunda familia
    assert "@font-face" not in css and "url(" not in css and "@import" not in css and not re.search(r"https?://", css)               # funciona sin internet
    assert set(re.findall(r"font-weight: (\d+)", css)) <= {"400", "500", "600"}                                                      # pesos 400, 500 (la afirmación) y 600
    assert "tabular-nums" in css and set(E.ESCALA_TIPOGRAFICA) >= {"nota", "cuerpo", "titulo_pagina", "titular"}


def test_radios_segun_el_papel_y_una_sola_sombra() -> None:
    import estilos as E

    css = E.css()
    assert (E.RADIO_TABLA, E.RADIO_CONTROL, E.RADIO_PANEL) == ("0", "8px", "14px") and len({E.RADIO_TABLA, E.RADIO_CONTROL, E.RADIO_PANEL}) == 3
    assert css.count("box-shadow:") == 1 and re.search(r"\.st-key-panel_principal[^{]*\{[^}]*box-shadow: var\(--sombra-panel\)", css)       # solo el panel principal y el detalle llevan sombra
    assert "var(--radio-tabla)" in css and "var(--radio-ctl)" in css and "var(--radio-panel)" in css


def test_sin_rasgos_de_plantilla() -> None:
    import estilos as E

    css = E.css()
    fuente = " ".join(p.read_text(encoding="utf-8") for p in [R / "app" / "secciones.py", R / "app" / "estilos.py", R / "app" / "app.py", *sorted((R / "app" / "paginas").glob("*.py"))])
    usos = re.findall(r"([^{}\n]*)\{[^}]*uppercase[^}]*\}", css)
    assert len(usos) == 2 and any(".aud-kicker" in u for u in usos) and any(".aud-cola-fila.cab" in u for u in usos), usos         # F29 (a pedido del usuario, según su referencia): solo el rótulo «Alertas de cámara» y el encabezado de la tabla de la cola
    assert css.count("linear-gradient") == 1 and "aud-sw.escala" in css                                              # el único degradado es la escala de la leyenda del mapa
    assert "arrow_forward" not in fuente and not re.search(r"→\s*[\"']", fuente)                                  # sin flechas al final de botones o enlaces
    assert "border-left: 3px" not in css and "inset 3px" not in css                                                  # sin franjas de acento
    assert "·" not in css                                                                                              # ni siquiera en el texto del cargador de archivos
    pie = E.pie("This application was made using the Waymo Open Dataset.", "Solución v3 congelada el 2026-11-14", 41)
    assert "·" not in pie and "·" not in E.leyenda_mapa(100) and "·" not in E.leyenda_estados()


def test_los_textos_visibles_no_usan_cadenas_con_puntos_medios() -> None:
    from waymo_evaluacion.ep3.app_logica import ATRIBUCION_WAYMO, texto_esfuerzo_cola, texto_resultado_cola

    assert "·" not in ATRIBUCION_WAYMO
    r = {"todos": True, "cobertura_dos": 0.702, "cobertura_uno": 0.62, "n_segmentos": 41, "segmento": "x", "hallados_dos": 1, "positivos_total": 2, "hallados_uno": 1, "flujo": "dos", "cajas_a_revisar": 10,
         "presupuesto": 0.2, "cajas_cola_total": 50, "horas": 1.0, "segundos": 20}
    assert "·" not in texto_resultado_cola(r) and "·" not in texto_esfuerzo_cola(r) and "·" not in texto_resultado_cola({**r, "todos": False})
    assert "Con auditoría previa (en muestra): unas" in texto_resultado_cola(r) and "Solo cola: unas" in texto_resultado_cola(r)


# ------------------------------------------------------------------------------------------------------------ paleta de curvas
def test_la_paleta_de_curvas_paso_la_validacion_de_dataviz_en_modo_oscuro() -> None:
    import estilos as E

    p = json.loads((R / "docs/ep3/f24_paleta_validacion.json").read_text(encoding="utf-8"))
    ad = p["paleta_adoptada"]
    assert ad["paleta"] == E.CURVAS_COLORES and p["modo"] == "dark" and p["superficie"] == E.TOKENS["panel"]            # la paleta validada es la que usa la página
    for clave in ("adyacentes", "todos_los_pares"):
        assert "ALL CHECKS PASS" in ad[clave] and "[FAIL]" not in ad[clave], clave
    assert "[FAIL]" in p["punto_de_partida_del_prompt"]["todos_los_pares"] and "[FAIL]" not in p["punto_de_partida_del_prompt"]["adyacentes"]          # el punto de partida pasaba los adyacentes y no el par azul-violeta
    cvd = float(re.search(r"worst all-pairs \S+↔\S+ ΔE ([\d.]+)", ad["todos_los_pares"]).group(1))
    normal = float(re.search(r"worst all-pairs \S+↔\S+ ΔE ([\d.]+) \(normal\)", ad["todos_los_pares"]).group(1))
    assert cvd >= 8 and normal >= 15                                                                                 # CVD >= 8 y visión normal >= 15 entre TODOS los pares
    assert len(set(E.CURVAS_COLORES)) == 5 and not any(c.upper() in (E.TOKENS["hueco"], E.TOKENS["aviso_texto"], E.TOKENS["sano"]) for c in E.CURVAS_COLORES)      # ninguna curva usa un color reservado
    r = p["rampa_del_mapa_de_calor"]
    assert r["pasos"] == E.RAMPA_SANA and "ALL CHECKS PASS" in r["ordinal"] and E.RAMPA_SANA[-1] == E.TOKENS["sano"]    # rampa teal validada: más claro = más proporción con pareja


# ------------------------------------------------------------------------------------------------------------ anillo y Resumen
def test_el_anillo_tiene_tres_estados_como_el_mapa_y_el_sin_datos_es_gris_plano() -> None:
    import estilos as E

    svg = E.anillo_camaras({1: "sana", 2: "sin_datos", 3: "hueco", 4: "sin_datos", 5: "sana"}, 300)
    assert svg.count('class="cu sana"') == 2 and svg.count('class="cu sin_datos"') == 2 and svg.count('class="cu hueco"') == 1 and svg.count('class="xx"') == 1          # el hueco lleva «X»; el sin datos, ninguna marca
    assert 'width="300"' in svg and "--nu:" in svg
    css = E.css()
    assert f"fill: var(--sin-datos)" in css and E.TOKENS["sin_datos"] == "#1B2740" and "hatch" not in css and "repeating-linear-gradient" not in css      # gris plano: sin rayado
    ley = E.leyenda_estados() + E.leyenda_mapa(100)
    assert all(x in ley for x in ("aud-sw sana", "aud-sw hueco", "aud-sw sin-datos", "Sana", "Hueco", "Sin datos")) and "rayado" not in ley             # la misma leyenda para el anillo y el mapa


def test_estado_camaras_segmento_usa_los_tres_estados_de_la_matriz() -> None:
    celdas = pd.DataFrame({"seg": ["s1", "s2"], "grupo": ["train", "test"]})
    for c in range(1, 6):
        celdas[f"tasa_c{c}"], celdas[f"n_rango_c{c}"], celdas[f"hueco_c{c}"] = 0.9, 150, False
    celdas.loc[0, ["tasa_c3", "hueco_c3"]] = [0.0, True]
    celdas.loc[0, "n_rango_c2"] = 40                                     # pocas cajas: sin datos
    celdas.loc[1, "n_rango_c5"] = 0
    m = matriz_calor(celdas)
    assert estado_camaras_segmento(m, "s1") == {1: "sana", 2: "sin_datos", 3: "hueco", 4: "sana", 5: "sana"}
    assert estado_camaras_segmento(m, "s2")[5] == "sin_datos" and set(estado_camaras_segmento(m, "s2").values()) == {"sana", "sin_datos"}
    assert estado_camaras_segmento(m, "no existe") == {c: "sin_datos" for c in CAMARAS}                              # sin fila: sin datos


def test_el_resumen_cabe_en_una_pantalla_de_1366_por_768() -> None:
    res = R / "docs/ep3/f23_fold_resumen.json"
    if not res.exists():
        pytest.skip("todavía no se midió el Resumen a 1366 x 768 (scripts/ep3/f23_medir_resumen.py)")
    m = json.loads(res.read_text(encoding="utf-8"))
    assert m["viewport"] == [1366, 768] and m["anillo_visible_completo"] and m["afirmacion_visible_completa"] and m["scroll_horizontal_px"] <= 0, m


# ------------------------------------------------------------------------------------------------------------ cola
def test_la_cola_trae_seis_columnas_y_el_detalle_siempre_visible(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    assert list(at.dataframe[0].value.columns) == ["Prioridad", "Segmento", "Caja", "Cámara", "Clase", "Prob. sin pareja", "Puntos sensor sup."]
    t = textos(at)
    assert "Prioridad 1 de" not in t and "**Caja " not in t                                                          # F32: sin selección el panel no ocupa espacio
    assert [x.label for x in at.tabs][0] == "Cola de cajas"                                                          # la lista es la primera pestaña
    at.session_state["tabla_cola"] = {"selection": {"rows": [0], "columns": [], "cells": []}}
    at.run()
    t = textos(at)
    assert not at.exception and "Prioridad 1 de" in t and "**Caja " in t
    assert 'class="cu activa"' in t or "Cámara de la caja" in t                                                       # el detalle ilumina la cámara de la caja
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert 'key="panel_detalle"' in fuente and 'st.columns([2.15, 1], gap="medium")' in fuente and 'key="panel_vacio"' not in fuente


def test_ningun_puntaje_sin_sentido_en_la_cola_ni_en_explica(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for seccion in ("Cola de revisión", "Explica una caja"):
        at = _abrir(entorno, monkeypatch, seccion)
        t = textos(at) + " " + " ".join(str(d.value.to_string()) for d in at.dataframe)
        assert not re.search(r"-\d{1,3},000\b|\b-?\d+,0{3,}\b", t.replace("<style>", "")), (seccion, re.findall(r".{12}-\d{1,3},000.{6}", t)[:2])        # nada tipo «-50,000»
    at = _abrir(entorno, monkeypatch, "Explica una caja")
    paso = " ".join(m.value for m in at.markdown if "aud-calculo" in m.value)
    assert "2 · Puntaje" in paso and "-50" in paso and "menos los puntos del sensor superior" in paso                      # F33: el puntaje vive en el paso 2 de «Cómo se calcula»


# ------------------------------------------------------------------------------------------------------------ auditoría
def test_la_auditoria_pinta_sin_datos_en_gris_plano_y_la_leyenda_coincide_con_el_anillo(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import estilos as E

    at = _abrir(entorno, monkeypatch, "Auditoría de cámaras")
    spec = " ".join(c.proto.spec for c in at.get("vega_lite_chart"))
    assert E.TOKENS["sin_datos"] in spec and "/ / /" not in spec                                                      # gris plano: sin rayado de texto
    assert E.TOKENS["sano"] in spec and E.RAMPA_SANA[0] in spec and E.TOKENS["hueco"] in spec                      # sana en teal (rampa) y hueco en coral
    t = textos(at)
    assert t.count('class="aud-leyenda fila"') == 1 and "aud-sw sin-datos" in t and "aud-sw hueco" in t and "Hueco" in t and "Sin datos (menos de 100 cajas)" in t and "aud-sw escala" in t         # F31: una línea con degradé
    assert "sin cajas o menos de 100 en el rango" in t.lower() and "no es lo mismo que 0 %" in t


# ------------------------------------------------------------------------------------------------------------ menos tarjetas
def test_solo_el_panel_principal_y_el_detalle_son_superficies_elevadas() -> None:
    import estilos as E

    css = E.css()
    assert css.count("background: var(--panel)") >= 1
    elevados = re.findall(r"([^{}]+)\{[^}]*box-shadow: var\(--sombra-panel\)", css)
    assert len(elevados) == 1 and all(c in elevados[0] for c in (".st-key-panel_principal", ".st-key-panel_detalle", ".st-key-panel_vacio"))
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert "border=True" not in fuente.replace("height=560, border=True, key=\"mapa_calor\"", "")                       # ningún contenedor envuelve una sola cosa con borde propio
    assert 'tarjeta_anillo' in fuente and ".aud-tarjeta-anillo { display: flex; flex-wrap: wrap; gap: .6rem 1rem; align-items: center; border-top" in css      # el anillo de la Auditoría va plano


# ------------------------------------------------------------------------------------------------------------ Validación > Selección
def test_los_criterios_de_seleccion_tienen_nombre_propio_y_leen_el_plan() -> None:
    c = criterios_seleccion()
    assert [k for k, _, _ in c] == ["O1", "O2", "O3", "O4"] and all(n and d for _, n, d in c)
    assert [n for _, n, _ in c] == ["Discrimina", "Vale la pena", "Recall en el punto A", "Estable y calibrada"]
    d = {k: x for k, _, x in c}
    plan = json.loads((R / "docs/ep3/plan_v3.json").read_text(encoding="utf-8"))
    assert F.decimal(plan["P8"]["objetivos"]["O1"]["auc_min"], 2) in d["O1"] and F.decimal(plan["P8"]["objetivos"]["O3"]["recall_punto_A_min"], 2) in d["O3"]       # umbrales del plan, no escritos a mano
    assert F.decimal(plan["P8"]["objetivos"]["O4"]["ece_max"], 2) in d["O4"]
    sin_plan = criterios_seleccion({})
    assert [k for k, _, _ in sin_plan] == ["O1", "O2", "O3", "O4"] and not any(ch.isdigit() for _, _, x in sin_plan for ch in x)                   # sin plan a mano, la definición sale sin números


def test_la_tabla_de_criterios_dice_cumple_o_no_cumple_con_texto_y_destaca_la_elegida() -> None:
    import estilos as E

    h = E.tabla_criterios(["Candidato", "AUC", "O1 Discrimina", "O2 Vale la pena"], [["Regla de puntos", "0,823", "Cumple", "No cumple"], ["LR", "0,797", "Cumple", "No cumple"]], elegida=0, columnas_cumple=(2, 3))
    assert h.count('<tr class="elegida">') == 1 and "Elegida" in h and h.count(">Cumple<") == 2 and h.count(">No cumple<") == 2
    assert 'class="cumple"' in h and 'class="no-cumple"' in h
    assert "color" not in re.sub(r'class="[^"]*"', "", h)                                                             # el cumplimiento es texto; el color solo lo refuerza


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_la_seleccion_real_usa_el_nombre_nuevo_de_la_regla_y_destaca_la_fila_elegida(monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir_real(monkeypatch, "Validación")
    for tab in at.tabs:
        if tab.label == "Selección":
            html = " ".join(m.value for m in tab.markdown)
            assert "Regla de puntos del sensor superior" in html and "Regla top" not in html
            assert re.search(r'<tr class="elegida"><td>Regla de puntos del sensor superior<span class="elegida-marca">Elegida</span>', html)
            assert "O1 Discrimina" in html and "O2 Vale la pena" in html and "O3 Recall en el punto A" in html and "O4 Estable y calibrada" in html
            assert html.count(">No cumple<") >= 1 and html.count(">Cumple<") >= 1


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_ninguna_pagina_muestra_el_nombre_interno_de_la_regla(monkeypatch: pytest.MonkeyPatch) -> None:
    from waymo_evaluacion.ep3.app_logica import SECCIONES

    at = _abrir_real(monkeypatch)
    for seccion in SECCIONES:
        ir_a(at, seccion)
        assert not at.exception, (seccion, at.exception)
        visible = " ".join([textos(at)] + [d.value.to_string() for d in at.dataframe] + [t.value.to_string() for t in at.table] + [c.proto.spec for c in at.get("vega_lite_chart")])
        assert "regla top" not in visible.lower(), (seccion, re.findall(r".{25}regla top.{15}", visible, flags=re.I)[:2])       # ni en las tablas, ni en los gráficos, ni en las leyendas


def test_el_nombre_visible_de_la_regla_no_cambia_ningun_identificador() -> None:
    assert F.nombre_visible("Regla top") == "Regla de puntos del sensor superior" and F.nombre_visible("solo para Regla top, LR3") == "solo para regla de puntos del sensor superior, LR3"
    assert F.nombre_visible("AUC: regla top 0,823.") == "AUC: regla de puntos del sensor superior 0,823." and F.nombre_visible("Con esto. Regla top gana").startswith("Con esto. Regla de puntos")
    assert F.nombre_visible("LR3") == "LR3" and F.nombre_visible(3) == 3
    from waymo_evaluacion.ep3.candidatos import CANDIDATOS, NIVEL_SIMPLICIDAD

    assert "Regla top" in CANDIDATOS and NIVEL_SIMPLICIDAD["Regla top"] == 0                                         # la clave de los datos sigue siendo «Regla top»
    t = F.tabla_legible(pd.DataFrame({"candidato": ["Regla top", "LR3"], "AUC": [0.823, 0.8]}))
    assert t["Candidato"].tolist() == ["Regla de puntos del sensor superior", "LR3"]


# ------------------------------------------------------------------------------------------------------------ Puntuar
def test_puntuar_pone_primero_las_acciones_y_la_especificacion_va_en_un_expander_cerrado(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Puntuar datos nuevos")
    exp = [e for e in at.expander if e.label == "Formato de los archivos de entrada"]
    assert len(exp) == 1 and exp[0].proto.expanded is False                                                          # cerrado por defecto
    assert len(at.get("file_uploader")) == 2 and any(b.label == "Usar un segmento de desarrollo de ejemplo" for b in at.button)
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    cuerpo = fuente[fuente.index("def puntuar("):fuente.index("# ------------------------------------------------------------------------------------------------------------ Ética")]
    assert cuerpo.index("_cargadores(plegado=") < cuerpo.index('st.expander("Formato de los archivos de entrada", expanded=False)')                    # las acciones van antes que la especificación
    assert "st.table(FORMATO_ARCHIVOS)" not in fuente[fuente.index("def _cargadores("):fuente.index("# ------------------------------------------------------------------------------------------------------------ Ética")]
    assert "Todavía no hay un segmento cargado" in textos(at)
    at.button[[b.label for b in at.button].index("Usar un segmento de desarrollo de ejemplo")].click().run()
    assert not at.exception and any("Cajas puntuadas" in m.value for m in at.markdown)                                  # el resultado sale al elegir el ejemplo
    encabezados = re.findall(r"<th[^>]*>([^<]*)</th>", " ".join(m.value for m in at.markdown))
    assert encabezados and not [c for c in encabezados if re.search(r"Key\.|\bpoints\b|\btype\b|\bmicros\b|Segment id", c)], encabezados           # sin encabezados técnicos en inglés
    assert ["Prioridad", "Caja", "Cámara", "Clase", "Prob. sin pareja", "Puntos sensor sup."] == [c for c in encabezados if c in ("Prioridad", "Caja", "Cámara", "Clase", "Prob. sin pareja", "Puntos sensor sup.")][:6]     # F35: las columnas de la Cola de revisión


# ------------------------------------------------------------------------------------------------------------ plan, sello y marcos
def test_el_plan_de_diseno_de_f23_declara_su_paleta_y_avisa_que_f24_la_supero() -> None:
    plan = (R / "docs/ep3/plan_diseno_f23.md").read_text(encoding="utf-8")
    for hexa in ("#F8F9FB", "#14202F", "#2457D6", "#0B6B74", "#B42318", "#C98A00", "#E3E6EB"):                           # los valores de la intención de F23, que quedan como historia
        assert hexa in plan.upper(), hexa
    assert "Cambria" in plan and "Revisión contra los defaults" in plan and "F24" in plan and "tema oscuro" in plan       # y el plan dice que F24 cambió la piel
    for pagina in ("### Resumen", "### Cola de revisión", "### Auditoría de cámaras"):
        assert pagina in plan


def test_la_integridad_del_sello_esta_registrada_y_el_script_solo_lee() -> None:
    antes = json.loads((R / "docs/ep3/f23_sello_antes.json").read_text(encoding="utf-8"))["archivos"]
    for clave in ("docs/ep3/plan_seleccion_ep3.sha256", "docs/ep3/plan_seleccion_ep3.json", "data/06_models_ep3/manifest_v3.json", "data/06_models_ep3/manifest_alternativas.json", "data/06_models_ep3/alternativas_v3.joblib"):
        assert clave in antes and len(antes[clave]) == 64, clave
    assert any(k.startswith("artefactos_ep3/") for k in antes) and any(k.startswith("notebooks/00b_") for k in antes)
    fuente = (R / "scripts/ep3/f23_integridad_sello.py").read_text(encoding="utf-8")
    assert "write_text" in fuente and fuente.count("write_text") == 2 and "subprocess.run([\"git\", *args]" in fuente and all(x not in fuente for x in ("\"add\"", "\"commit\"", "\"push\"", "\"checkout\"", "\"reset\"", "\"stash\""))
