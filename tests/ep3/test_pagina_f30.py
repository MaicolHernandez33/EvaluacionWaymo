"""F30: ajustes del Resumen (sin el enlace de la Auditoría, recuadro de alertas ajustado con el anillo arriba, pie sin la línea de validación) y fin del Modo presentación.
Cubre: que el modo no deje rastro en la interfaz, los textos ni el código; «Impacto estimado» como sección fija de Validación › En muestra; los textos corregidos de Ética y Ayuda; el pie del Resumen;
las medidas del bloque y la carpeta de revisión. Escribe solo en ``tmp_path``."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from tests.ep3.test_app import textos
from tests.ep3.test_pagina_f24 import _abrir, _sin_css, entorno  # noqa: F401  (``entorno`` es la fixture del módulo de F24)

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))
PROHIBIDO = re.compile(r"modo[ _]presentaci[oó]n|presentacion|escala: 1\.18", re.I)


# ------------------------------------------------------------------------------------------------------------ el modo no deja rastro
def test_el_modo_presentacion_no_deja_rastro_en_la_aplicacion() -> None:
    for p in [*sorted((R / "app").rglob("*.py")), R / "src/waymo_evaluacion/ep3/app_logica.py"]:
        t = p.read_text(encoding="utf-8")
        assert not PROHIBIDO.search(t), (p.name, PROHIBIDO.search(t).group(0))
    import waymo_evaluacion.ep3.app_logica as A

    assert not hasattr(A, "ocultar_identificadores") and not hasattr(A, "IDENTIFICADORES")
    import inspect

    import estilos as E

    assert "presentacion" not in inspect.signature(A.tabla_cola).parameters and "presentacion" not in inspect.signature(A.tabla_por_objeto).parameters
    assert "presentacion" not in inspect.signature(E.css).parameters and "presentacion" not in inspect.signature(E.metricas).parameters and not hasattr(E, "PRESENTACION")
    assert "--escala: 1.18" not in E.css() and ".pres" not in E.css()


def test_la_barra_lateral_solo_tiene_el_rol_y_ninguna_pagina_guarda_un_estado_del_modo(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    from waymo_evaluacion.ep3.app_logica import SECCIONES

    at = _abrir(entorno, monkeypatch, "Resumen")
    assert [s.label for s in at.sidebar.selectbox] == ["Rol"] and list(at.sidebar.toggle) == [] and list(at.sidebar.checkbox) == []
    assert "presentacion" not in at.session_state
    for s in SECCIONES:
        from tests.ep3.test_app import ir_a

        ir_a(at, s)
        assert not at.exception, (s, at.exception)
        assert not PROHIBIDO.search(textos(at)) and "presentacion" not in at.session_state, s


def test_ninguna_tabla_ni_descarga_oculta_identificadores_por_un_modo(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert "vista.lista_B" in (R / "src/waymo_evaluacion/ep3/puntuar.py").read_text(encoding="utf-8") and 'ctx["presentacion"]' not in fuente and "(oculto)" not in fuente
    from waymo_evaluacion.ep3.app_logica import cargar_datos, resumen_cola, tabla_cola

    d = cargar_datos(entorno / "datos")
    r = resumen_cola(d["cajas"], d["curva"], "sol", "Todos", 0.2, 20)
    assert {"Segmento", "Marca de tiempo", "Identificador de objeto"} <= set(tabla_cola(r["top"], r["cajas_cola_total"], {}).columns)         # los identificadores siempre están en los datos que se descargan


# ------------------------------------------------------------------------------------------------------------ textos corregidos
def test_etica_y_ayuda_ya_no_hablan_del_modo_y_el_rol_solo_cambia_la_pagina(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    etica = _sin_css(textos(_abrir(entorno, monkeypatch, "Ética y límites")))
    assert "identificadores de objeto y marcas de tiempo" in etica and "Nada se guarda ni se envía" in etica and not PROHIBIDO.search(etica) and "los oculta" not in etica
    ayuda = _sin_css(textos(_abrir(entorno, monkeypatch, "Ayuda y glosario")))
    assert "cambia la página que se abre." in ayuda and "alerta que se muestra primero" not in ayuda and not PROHIBIDO.search(ayuda) and "agranda la letra" not in ayuda
    from waymo_evaluacion.ep3.app_logica import TEXTOS_ENTORNO

    for variante in TEXTOS_ENTORNO.values():                                                                                 # las dos variantes de EP3_ENTORNO
        assert "presentación" not in variante["consideracion_etica"] and "identificadores de objeto y marcas de tiempo" in variante["consideracion_etica"]


# ------------------------------------------------------------------------------------------------------------ Impacto estimado en Validación
def test_impacto_estimado_es_una_seccion_fija_de_validacion_en_muestra_con_su_fuente(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Validación")
    pestana = next(t for t in at.tabs if t.label == "En muestra")
    en_pestana = " ".join(m.value for m in pestana.markdown) + " " + " ".join(c.value for c in pestana.caption)
    assert "Impacto estimado" in en_pestana and "≈" in en_pestana and "Estimación:" in en_pestana and "supuesto, no medido" in en_pestana and "Informe técnico de EP3" in en_pestana
    otras = [t for t in at.tabs if t.label != "En muestra"]
    assert all("Impacto estimado" not in " ".join(m.value for m in t.markdown) for t in otras)                              # una sola vez, en su pestaña
    assert "Impacto estimado" not in textos(_abrir(entorno, monkeypatch, "Resumen"))


def test_el_impacto_estimado_va_antes_del_grafico_de_la_pestana() -> None:
    """F34 reemplaza a F30: en «En muestra» el orden es aviso, lectura, «Impacto estimado», «De dónde viene la mejora de la auditoría» y, al final, el gráfico (como en la maqueta de F34)."""
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    cuerpo = fuente[fuente.index("def validacion("):fuente.index("# ---", fuente.index("def validacion("))]
    assert cuerpo.index("_impacto_estimado(") < cuerpo.index("De dónde viene la mejora de la auditoría") < cuerpo.index('_grafico_validacion("posthoc"') and "# pestaña: En muestra" in cuerpo


# ------------------------------------------------------------------------------------------------------------ Resumen
def test_el_resumen_ya_no_tiene_el_enlace_de_la_auditoria_ni_la_linea_de_validacion_en_el_pie(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    from waymo_evaluacion.ep3.app_logica import ATRIBUCION_WAYMO

    at = _abrir(entorno, monkeypatch, "Resumen")
    t = _sin_css(textos(at))
    for salio in ("Abrir la auditoría de cámaras", "Ver en Validación", "Validación externa pendiente", "las cifras salen de segmentos de desarrollo"):
        assert salio not in t, salio
    assert ATRIBUCION_WAYMO in t and "Solución v3 congelada" in t and "Datos de desarrollo" in t                              # el pie global se queda
    assert not any(getattr(b, "label", "") in ("Abrir la auditoría de cámaras", "Ver en Validación") for b in at.button)
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert "_pie_resumen" not in fuente and "enlace_auditoria" not in fuente and "enlace_validacion" not in fuente and "ENLACE_AUDITORIA" not in fuente
    assert all(x in fuente for x in ("Auditar", "ACCION_AUDITAR")) and 'ARCHIVO_PAGINA["Cola de revisión"], label=ENLACE_COLA' in fuente         # «Auditar» sigue en cada fila; el enlace de la cola completa se mantiene


def test_el_anillo_va_arriba_en_la_columna_derecha_y_el_bloque_no_tiene_cabecera_aparte() -> None:
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    cuerpo = fuente[fuente.index("def _bloque_alertas("):fuente.index("def _bloque_cola(")]
    assert 'izq, der = st.columns([1.4, 1], gap="large", vertical_alignment="top")' in cuerpo                                  # dos columnas, la derecha alineada arriba
    izq, der = cuerpo[cuerpo.index("with izq:"):cuerpo.index("with der:")], cuerpo[cuerpo.index("with der:"):]
    assert all(x in izq for x in ("E.kicker(KICKER_ALERTAS)", "_titular_alertas(n)", "sub", "key=f\"auditar_{i}\"")) and "bloque_anillo" not in izq
    assert "Cámaras del segmento" in der and "E.bloque_anillo(estados, TAMANO_ANILLO_RESUMEN" in der and cuerpo.index("Cámaras del segmento") < cuerpo.index("bloque_anillo(")        # rótulo encima, leyenda debajo (la trae el bloque)
    assert "cab, enl" not in cuerpo and "st.page_link" not in cuerpo


def test_el_anillo_mide_entre_240_y_260_px_y_el_panel_se_ajusta_al_contenido() -> None:
    import secciones as S
    import estilos as E

    assert 240 <= S.TAMANO_ANILLO_RESUMEN <= 260
    assert "padding: 1rem 1.4rem 1rem 1.4rem" in E.css() and "padding: 1.3rem 1.5rem 24px" not in E.css()                      # menos relleno: el recuadro mide lo que mide su contenido


def test_el_bloque_de_alertas_se_midio_antes_y_despues_y_la_cola_se_ve_en_la_primera_pantalla() -> None:
    p = R / "docs/ep3/f30_altura_bloque.json"
    if not p.exists():
        pytest.skip("todavía no se midió el bloque (scripts/ep3/f30_medir_bloque.py)")
    m = json.loads(p.read_text(encoding="utf-8"))
    assert {"antes", "despues"} <= set(m)
    assert m["despues"]["alto_del_bloque_px"] < m["antes"]["alto_del_bloque_px"] and m["diferencia_alto_del_bloque_px"] < 0
    assert m["despues"]["alto_ventana"] == 768 and not m["despues"]["enlace_en_el_bloque"]
    assert m["despues"]["titulo_y_filtros_visibles_en_768"], m["despues"]                                                     # meta de F30: el título de la cola y sus filtros, sin desplazarse
    assert 240 <= m["despues"]["tamano_del_anillo_px"] <= 260 and m["despues"]["rotulo_del_anillo"]["arriba"] - m["despues"]["panel"]["arriba"] <= 40                  # el anillo (con su rótulo) arranca arriba, junto al borde superior del bloque


# ------------------------------------------------------------------------------------------------------------ capturas y carpeta de revisión
def test_no_hay_capturas_ni_pasos_del_modo_presentacion() -> None:
    assert not [p.name for p in (R / "images/ep3/pagina").rglob("*") if "presentacion" in p.name.lower()]
    for s in ("capturar_pagina.py", "f24_medir_resumen.py", "f25_medir_barra.py", "f26_capturas_extra.py", "f30_medir_bloque.py"):
        t = (R / "scripts/ep3" / s).read_text(encoding="utf-8")
        assert not re.search(r"modo[ _]presentaci[oó]n|presentacion|--escala: 1\.18|JS_POS_INTERRUPTOR", t, re.I), s


ESPERADOS_PARA_REVISION = ["01_resumen_1366.png", "01_resumen_1366x768.png", "02_auditoria_de_camaras_1366.png", "03_cola_de_revision_1366.png", "03_cola_de_revision_sin_seleccion_1366.png", "02b_curvas_sin_referencia.png",
                           "04_explica_una_caja_1366.png", "05_validacion_hiperparametros_1366.png", "05_validacion_ensambles_1366.png", "05_validacion_generalizacion_1366.png", "05_validacion_seleccion_1366.png",
                           "05_validacion_no_supervisado_1366.png", "05_validacion_en_muestra_1366.png", "06_puntuar_datos_nuevos_1366.png", "07_etica_y_limites_1366.png", "08_ayuda_y_glosario_1366.png", "REPORTE_F30.md"]


def test_la_carpeta_para_revision_tiene_exactamente_los_17_archivos_pedidos() -> None:
    carpeta = R / "images/ep3/pagina/para_revision"
    if not carpeta.exists():
        pytest.skip("todavía no se armó la carpeta (scripts/ep3/armar_para_revision.py)")
    assert sorted(p.name for p in carpeta.iterdir()) == sorted(ESPERADOS_PARA_REVISION) and len(ESPERADOS_PARA_REVISION) == 17
    assert all(p.stat().st_size > 1000 for p in carpeta.iterdir())
