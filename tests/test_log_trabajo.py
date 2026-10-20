"""Pruebas del log de trabajo (docs/log_trabajo_ep2.md): nota inicial y fecha en cada entrada."""
import re
from pathlib import Path

R = Path(__file__).resolve().parent.parent
LOG = R / "docs" / "log_trabajo_ep2.md"


def test_log_con_nota_inicial_y_fecha_en_cada_entrada():
    texto = LOG.read_text(encoding="utf-8")
    assert "Log cronológico; las entradas antiguas pueden estar superadas por las posteriores. Las cifras vigentes están en el informe técnico." in texto.split("- [")[0]
    entradas = [l for l in texto.splitlines() if l.startswith("- [")]
    assert entradas, "el log no tiene entradas"
    for l in entradas:
        assert re.match(r"- \[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] ", l), f"entrada sin fecha: {l[:60]}"
    fechas = [l[3:22] for l in entradas]
    assert fechas == sorted(fechas), "las entradas del log no están en orden cronológico"
