"""Pruebas del informe tecnico: el script corre, la seccion 7 queda poblada y las tablas Markdown son consistentes.

Estas pruebas usan los archivos de salida de los notebooks (data/08_reporting, docs/); como `data/` no esta en git,
se omiten si esos archivos no existen.
"""
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

R = Path(__file__).resolve().parent.parent
JSON_NS = R / "data" / "08_reporting" / "08_no_supervisado_resumen.json"
HAY_DATOS = JSON_NS.exists() and (R / "data" / "08_reporting" / "10_resumen_cifras.json").exists()
pytestmark = pytest.mark.skipif(not HAY_DATOS, reason="faltan los archivos de salida de los notebooks (data/ no esta en git)")


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, R / "scripts" / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _seccion(texto, n):
    m = re.search(rf"^## {n}\. .*?(?=^## {n + 1}\. )", texto, flags=re.S | re.M)
    assert m, f"no se encontro la seccion {n} del informe"
    return m.group(0)


@pytest.fixture(scope="module")
def informe():
    r = subprocess.run([sys.executable, "-X", "utf8", str(R / "scripts" / "generar_informe_tecnico.py")], cwd=R, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, f"el script fallo:\n{r.stdout}\n{r.stderr}"
    return (R / "docs" / "informe_tecnico_EP2.md").read_text(encoding="utf-8")


def test_seccion_7_tiene_todas_las_cifras(informe):
    s7 = _seccion(informe, 7)
    assert re.search(r"Concordancia entre técnicas \(ARI\): KMeans vs GMM \d,\d{3}, KMeans vs jerarquico \d,\d{3}, GMM vs jerarquico \d,\d{3}", s7)
    assert re.search(r"Estabilidad por segmento \(\d+ remuestreos\): ARI medio \d,\d{3} y mínimo \d,\d{3}", s7)
    assert re.search(r"IsolationForest marca [\d.]+ cajas atípicas \(\d+ %\) en \d+ segmentos, con tasa de `sin_camara` [\d,]+ % frente a [\d,]+ % en el resto", s7)
    assert re.search(r"Diferencia con signo entre los dos clusters en la tasa de `sin_camara`: [\d,]+ puntos \(IC 95 % por segmentos [\d,]+ a [\d,]+; excluye 0\)", s7)
    assert re.search(r"El k elegido por máximo silhouette de KMeans es \d+\.", s7)
    for malo in ("(sin dato)", "nan", "None", "{", "}"):
        assert malo not in s7.replace("{sin_camara}", ""), f"la seccion 7 contiene '{malo}'"


def test_extractor_falla_con_mensaje_claro_si_falta_una_linea():
    ext = _cargar("extraer_no_supervisado_08")
    with pytest.raises(SystemExit) as e:
        ext.extraer("Concordancia entre tecnicas (ARI): {'KMeans vs GMM': 0.99}\n")
    msg = str(e.value)
    assert "no se encontro la linea" in msg and "IsolationForest" in msg


def test_informe_sin_tablas_desiguales(informe):
    ver = _cargar("verificar_tablas_markdown")
    for ruta in ("docs/informe_tecnico_EP2.md", "docs/evaluacion_final_B.md"):
        total, malas = ver.analizar(R / ruta)
        assert total > 0
        assert not malas, f"{ruta} tiene tablas con filas de distinto numero de celdas: {malas}"


def test_cifras_previas_del_07_estan_rotuladas(informe):
    # toda aparicion de las cifras de la version previa del 07 debe estar junto a un rotulo de version previa
    for cifra in ("-11.4", "-19.0 a -6.1"):
        for m in re.finditer(re.escape(cifra), informe):
            ventana = informe[max(0, m.start() - 700): m.end() + 700].lower()
            assert "versión previa" in ventana or "version previa" in ventana, f"la cifra {cifra} aparece sin rotulo de version previa"


def test_sin_razon_numerica_inestable_y_con_cifras_del_07_rotuladas(informe):
    docs = (R / "docs" / "evaluacion_final_B.md").read_text(encoding="utf-8")
    assert "772,22" not in informe and "772,22" not in docs
    for cifra in ("265.377 filas", "2,09 % ciclistas"):
        for m in re.finditer(re.escape(cifra), informe):
            assert "sin archivo de salida" in informe[m.start(): m.end() + 120], f"{cifra} sin rotulo"
    assert "7.314" not in informe and "7.367" not in informe          # cifras de la NHTSA: el 07 no da el nombre del documento
    assert "Límite del intervalo de la Fracción para 80 %" in informe


def test_ronda_2_formato_constante_y_secciones(informe):
    ctes = _cargar("constantes_ep2")
    n = ctes.EJECUCIONES_TEST
    nb = (R / "notebooks" / "10_evaluacion_final_sin_camara.ipynb").read_text(encoding="utf-8")
    assert f"ejecuciones 2 a {n} de {n}" in nb, "K.1 del notebook no coincide con la constante EJECUCIONES_TEST"
    assert f"sobre el test {n} veces" in informe                                          # seccion 9 y 11 leen la misma constante
    assert "### Mapa de la rúbrica" in informe and informe.index("### Mapa de la rúbrica") < informe.index("## 2. Problema")
    assert "{'Dawn/Dusk'" not in informe                                                  # sin diccionarios crudos en prosa
    assert "-25,000" not in informe and "object_type_" not in informe
    assert "102.124.064.984" not in informe                                               # los identificadores de segmento no llevan separador de miles
    s3 = _seccion(informe, 3)
    assert "366.314" in s3 and "64.509" in s3 and "68.555" in s3 and "16.062" in s3 and "17.297" in s3 and "3.734" in s3 and "4.378" in s3
    assert "no por `sin_camara`" in s3 and "no se usaron en el modelado; solo en un análisis descriptivo post hoc (sección 7)" in s3
    assert "Tabla 3 de Sun et al. (2020)" in _seccion(informe, 6)
    assert "Fuentes citadas en los notebooks 07 y 08 y en este informe" in informe
    assert "p de Fisher" not in informe.split("### 14.1")[1].split("### 14.2")[0]
    assert "Desviaciones respecto del plan v2" not in informe                                # sin titulos duplicados copiados de los notebooks


def test_cierre_del_informe(informe):
    s10, s7, s13 = _seccion(informe, 10), _seccion(informe, 7), informe.split('## 14. Anexos')[1]
    punto1 = s10[s10.index("1. **Auditoría por segmento y cámara.**"): s10.index("2. **Priorización")]
    assert "reúnen solo el" in punto1 and "reúnen solo el" not in s10.split("**Riesgos de equidad medidos.**")[1].split("**Monitoreo")[0]
    assert "los segmentos de lluvia usan todos sus frames y train usa solo los etiquetados" in s7
    assert "primeras filas del diagnóstico" not in informe
    assert "NHTSA, publicaciones 813727 y 813818 (2023), usadas en el 07 solo como contexto" in s13
    assert "crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813727" in s13 and "ViewPublication/813818" in s13


def test_secciones_nuevas_del_informe(informe):
    s2, s3, s4, s8, s11 = _seccion(informe, 2), _seccion(informe, 3), _seccion(informe, 4), _seccion(informe, 8), _seccion(informe, 11)
    assert "### 2.1 Objetivos" in s2 and "### 2.2 KPIs" in s2
    kpi = s2.split("### 2.2 KPIs")[1]
    for k in ("AUC", "PR-AUC", "Fracción para 80 %", "Recall en el punto A", "% de cajas revisadas en el punto A", "ECE (calibración)", "Estabilidad por fold", "Estabilidad por segmento"):
        assert f"| {k} |" in kpi, f"falta el KPI {k}"
    assert "### Preparación y calidad de los datos" in s3 and "Tratamiento en la regresión logística" in s3
    assert s4.count("| 1. Entendimiento del negocio |") == 1 and "| 6. Despliegue |" in s4
    assert "### Por qué estos algoritmos y esta configuración" in s8 and "No usamos SMOTE" in s8
    assert "### Lectura de negocio" in _seccion(informe, 7)
    assert s11.startswith("## 11. Ética, sesgos y privacidad") and "Riesgo de uso" in s11
    assert "Ética, sesgos y privacidad" in informe.split("### Mapa de la rúbrica")[1].split("## 2.")[0] or "Sección 11" in informe or "11 (ética" in informe


def test_archivos_congelados_coinciden_con_el_plan_v2():
    r = subprocess.run([sys.executable, "-X", "utf8", str(R / "scripts" / "verificar_congelados.py")], cwd=R, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "coinciden 14 de 14 archivos" in r.stdout
