"""Seguridad de la pagina (solo lectura): escucha solo en localhost, barra minima y puerto publicado solo en el equipo.

Lee .streamlit/config.toml, scripts/ep3/arrancar_app.bat (y .ps1), Dockerfile y docker-compose.yml; no escribe nada.
Si alguien cambia estos archivos y expone la pagina en la red, estas pruebas fallan.
"""
from __future__ import annotations

import re
from pathlib import Path

R = Path(__file__).resolve().parents[2]


def _toml_simple(texto: str) -> dict[str, dict[str, str]]:
    """Lector minimo de tablas [seccion] con claves `k = valor` (basta para este archivo; Python 3.10 no trae tomllib)."""
    out: dict[str, dict[str, str]] = {}
    sec = ""
    for linea in texto.splitlines():
        s = linea.split("#", 1)[0].strip()
        if not s:
            continue
        m = re.fullmatch(r"\[(\w+)\]", s)
        if m:
            sec = m.group(1)
            out.setdefault(sec, {})
            continue
        if "=" in s:
            k, v = (x.strip() for x in s.split("=", 1))
            out.setdefault(sec, {})[k] = v.strip('"')
    return out


def test_config_streamlit_escucha_solo_en_localhost():
    cfg = _toml_simple((R / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert cfg["server"]["address"] == "localhost"
    assert cfg["server"]["headless"] == "false"
    assert cfg["browser"]["gatherUsageStats"] == "false"
    assert cfg["client"]["toolbarMode"] == "minimal"


def test_arranque_local_usa_localhost_y_sin_telemetria():
    for nombre in ("arrancar_app.bat", "arrancar_app.ps1"):
        t = (R / "scripts" / "ep3" / nombre).read_text(encoding="utf-8")
        m = re.search(r"--server\.address[ =](\S+)", t)
        assert m and m.group(1) == "localhost", f"{nombre}: la pagina debe escuchar solo en localhost"
        assert "0.0.0.0" not in t, nombre
        assert re.search(r"--browser\.gatherUsageStats[ =]false", t), f"{nombre}: falta desactivar la telemetria"


def test_compose_publica_el_puerto_solo_en_el_equipo():
    t = (R / "docker-compose.yml").read_text(encoding="utf-8")
    lineas = [l.strip() for l in t.splitlines() if not l.strip().startswith("#")]
    puertos = [l.lstrip("- ").strip().strip('"') for l in lineas if re.match(r"-\s*\"?\d*\.?\d*\.?\d*\.?\d*:?\d+:\d+\"?$", l)]
    assert puertos, "no se encontro la seccion ports"
    for pto in puertos:
        assert pto.startswith("127.0.0.1:"), f"puerto publicado sin 127.0.0.1: {pto}"


def test_dockerfile_solo_abre_0000_dentro_del_contenedor_y_dockerignore_excluye_data():
    d = (R / "Dockerfile").read_text(encoding="utf-8")
    assert "--server.address=0.0.0.0" in d  # dentro del contenedor es necesario; el compose lo limita a 127.0.0.1
    ig = (R / ".dockerignore").read_text(encoding="utf-8").splitlines()
    assert "*" in ig and "data/" in ig and "*.parquet" in ig and "*.joblib" in ig
    assert not any(l.strip().startswith("!data") for l in ig)
