"""Pruebas de sincronía entre README.md y docs/informe_tecnico_EP2.md: las cifras y frases clave tienen que decir lo mismo en los dos.

Fallan si uno de los dos documentos vuelve a diferir del otro en segmentos de lluvia, 41/91, los 20 s por revisión, la unidad de revisión,
los logaritmos de la regresión logística o los nombres de modelos (con tilde). Los valores esperados se calculan aquí desde los archivos, no se escriben a mano.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

R = Path(__file__).resolve().parent.parent
HAY_DATOS = all((R / p).exists() for p in ("data/08_reporting/10_resumen_cifras.json", "data/08_reporting/pytest_resumen.json", "data/08_reporting/ep1_pruebas_cobertura.json", "data/05_model_input/features_B.parquet"))
pytestmark = pytest.mark.skipif(not HAY_DATOS, reason="faltan los archivos de salida de los notebooks (data/ no esta en git)")


def _correr(script):
    r = subprocess.run([sys.executable, "-X", "utf8", str(R / "scripts" / script)], cwd=R, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, f"{script} fallo:\n{r.stdout}\n{r.stderr}"


@pytest.fixture(scope="module")
def docs():
    _correr("generar_informe_tecnico.py")          # el README lee bloques del informe ya generado
    _correr("generar_readme.py")
    return (R / "README.md").read_text(encoding="utf-8"), (R / "docs" / "informe_tecnico_EP2.md").read_text(encoding="utf-8")


def _plano(t):
    return re.sub(r"\s+", " ", t)


def _parrafo(texto, inicio):
    m = re.search(rf"{re.escape(inicio)}[^\n]*", texto)
    assert m, f"no hay un párrafo que empiece con {inicio!r}"
    return m.group(0)


def test_segmentos_de_lluvia_igual_en_los_dos(docs):
    readme, informe = docs
    seg = pd.read_csv(R / "docs/seleccion_segmentos/segmentos_ep2.csv", dtype=str)
    reg = pd.read_csv(R / "docs/seleccion_segmentos/registro_verificacion_ep2.csv", dtype=str)
    dia = pd.read_csv(R / "docs/seleccion_segmentos/diagnostico_lluvia_ep2.csv", dtype={"segment_id": str})
    lluvia = seg[seg["uso"] == "solo_clustering"]
    vacia = int(lluvia["motivo"].str.startswith("asociacion vacia").sum())
    ralo = int(lluvia["motivo"].str.startswith("etiquetado ralo").sum())
    assert vacia + ralo == len(lluvia) and vacia < len(lluvia)                          # no todos tienen la asociación vacía
    frase = f"Los {len(lluvia)} segmentos de lluvia no forman parte de esos {len(reg)}: son un estrato aparte ({vacia} con asociación vacía y {ralo} con etiquetado ralo)"
    assert frase in _plano(readme) and frase in _plano(informe)
    frames_ralo = int(dia[dia["motivo"].str.startswith("etiquetado ralo")]["frames_etiquetados"].sum())
    assert f"{ralo} tiene {frames_ralo} frames etiquetados" in _plano(informe)           # la sección 7 del informe dice lo mismo que la 3
    assert informe.count("no tienen frames etiquetados (asociación vacía)") >= 2        # secciones 3 y 7
    assert "como estos segmentos no tienen frames etiquetados" not in informe and "tienen la tabla de asociación vacía (" not in informe


def test_41_de_91_igual_en_los_dos(docs):
    readme, informe = docs
    reg = pd.read_csv(R / "docs/seleccion_segmentos/registro_verificacion_ep2.csv", dtype=str)
    n, sel = len(reg), int((reg["resultado"] == "seleccionado").sum())
    assert re.search(rf"De {n} segmentos evaluados.{{0,60}}?, {sel} cumplen", readme)
    assert re.search(rf"Evaluamos {n} segmentos.{{0,60}}? y seleccionamos {sel} para", informe)
    assert f"los otros {n - sel} se descartaron" in readme


def test_20_segundos_igual_en_los_dos(docs):
    readme, informe = docs
    nb = json.loads((R / "notebooks/07_decision_target_ep2.ipynb").read_text(encoding="utf-8"))
    s = next(int(m.group(1)) for c in nb["cells"] if c["cell_type"] == "code" for m in [re.search(r"^SEGUNDOS_POR_REVISION\s*=\s*(\d+)", "".join(c["source"]), flags=re.M)] if m)
    frase = (f"Los {s} s por revisión no se calcularon ni se midieron: son un supuesto editable que fijamos en el notebook 07 (`SEGUNDOS_POR_REVISION`), "
             "sin fuente citada, y que el 09 y el 10 repiten como constante")
    assert frase in _plano(readme) and frase in _plano(informe)
    assert f"Las horas son cajas × {s} s ÷ 3.600" in readme and f"Las horas son cajas × {s} s ÷ 3.600" in informe
    assert f"el supuesto de {s} s por revisión viene del 09," in informe and "que lo copia del 07, donde se fijó" in informe       # el texto citado del 10 dice «del 09»
    assert f"(supuesto del 09)" not in informe


def test_unidad_de_revision_igual_en_los_dos(docs):
    readme, informe = docs
    pr, pi = _parrafo(readme, "**Unidad de revisión: la caja, no el frame.**"), _parrafo(informe, "**Unidad de revisión: la caja, no el frame.**")
    assert pr == pi
    for kpi in ("% de cajas revisadas en el punto A", "Fracción de cajas a revisar"):
        assert kpi in readme and kpi in informe
    assert "| % de frames revisados en el punto A |" not in informe and "| % de frames revisados en el punto A |" not in readme


def test_logaritmos_igual_en_los_dos(docs):
    readme, informe = docs
    hip = json.loads((R / "data/06_models/hiperparametros_B.json").read_text(encoding="utf-8"))
    pre = hip["preprocesamiento_lr"]
    con = ", ".join(f"`{c}`" for c in pre["log1p_y_estandarizacion"])
    frase = (f"la regresión logística aplica `log1p` y luego estandariza {len(pre['log1p_y_estandarizacion'])} variables ({con}) y solo estandariza las otras {len(pre['estandarizacion'])}; "
             "los árboles (HGB y Random Forest) usan las variables sin transformar; el aprendizaje no supervisado usa los logaritmos de puntos, densidad y volumen")
    assert frase in _plano(informe) and frase[0].upper() + frase[1:] in _plano(readme)
    assert "se usan solo en el aprendizaje no supervisado" not in informe and "solo en el no supervisado" not in readme


def test_nombres_de_modelos_con_tilde_en_los_dos(docs):
    for texto in docs:
        for sin in ("Regresion logistica", "Regla geometrica", "Isotonica", "Modelo minimo"):
            assert sin not in texto, f"nombre sin tilde: {sin}"
    readme, informe = docs
    for con in ("Regresión logística", "Regla geométrica (azimut > 105 primero)", "Isotónica"):
        assert con in readme and con in informe


def test_nota_de_reglas_identicas_y_class_weight_en_el_informe(docs):
    readme, informe = docs
    nota = _parrafo(informe, "**Por qué dos filas son idénticas.**")
    assert nota == _parrafo(readme, "**Por qué dos filas son idénticas.**")
    cw = pd.read_csv(R / "data/08_reporting/09_class_weight.csv", keep_default_na=False)
    h = cw[(cw["modelo"] == "HGB")].set_index("class_weight")["mejor PR-AUC interno (promedio de folds)"]
    assert round(float(h["None"]), 3) == round(float(h["balanced"]), 3) and float(h["balanced"]) > float(h["None"])      # empate a 3 decimales; gana balanced
    assert "empate a 3 decimales; gana balanced por" in informe and "Por qué el HGB quedó sin peso aunque la tabla dé como ganador a balanced" in informe
    por_fold = pd.read_csv(R / "data/08_reporting/09_hiperparametros_por_fold.csv", keep_default_na=False)
    hg = por_fold[por_fold["modelo"] == "HGB"]["class_weight"]
    assert f"el HGB eligió balanced en {int((hg == 'balanced').sum())} de {len(hg)} folds y sin peso en {int((hg != 'balanced').sum())}" in _plano(informe)


def test_sensibilidad_120_en_el_readme(docs):
    readme, _ = docs
    c = pd.read_csv(R / "data/08_reporting/10_comparacion_120.csv")
    cumple = {(m, b): v == "si" for m, b, v in zip(c["modelo"], c["base"], c["vale la pena"])}
    geo = [b for b in c["base"].unique() if b.startswith("Regla geometrica")][0]
    assert cumple[("HGB", "Regla: menos puntos top")] and cumple[("Random Forest", "Regla: menos puntos top")]
    assert not any(v for (m, b), v in cumple.items() if b == geo)
    assert "**Sensibilidad a 120°" in readme and "El HGB y el Random Forest cumplen «vale la pena» frente a la regla por puntos top, pero no frente a la regla geométrica" in readme
    assert "da ninguno" in readme.split("**Sensibilidad a 120°")[1].split("**Equidad")[0]
    titular = [l for l in readme.split("## 8. ")[1].splitlines() if l.startswith("> ")][0]
    assert "comparación principal" in titular


def test_marcador_del_canal_de_entrega(docs):
    readme, _ = docs
    assert "se entrega aparte del repositorio, por el AVA / Moodle del curso MLY1101 (DuoC UC)." in readme and "<CANAL" not in readme and "COMPLETA" not in readme and "por confirmar" not in readme
