"""F38: compara el README anterior con el nuevo y escribe ``diff_resumen.txt``: por sección (líneas antes y después, qué se agregó, qué se movió o cambió de redacción) y la lista de cifras y advertencias
que había antes frente a las de ahora (si falta alguna, la dice). Solo lee.
Uso: .venv\Scripts\python scripts/ep3/f38_diff_readme.py --antes <README anterior> --despues README.md --salida <diff_resumen.txt>
"""
from __future__ import annotations

import argparse
import difflib
import re
from pathlib import Path

NUM = re.compile(r"(?<![\w.,])\d[\d.]*(?:,\d+)?(?: ?%)?")
ADV = re.compile(r"post hoc, no pre-declarado|sin validación con datos nuevos|en muestra|no es una prueba ciega|supuesto", re.I)


def secciones(texto: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"0. Portada (antes del índice y de la sección 1)": []}
    clave = "0. Portada (antes del índice y de la sección 1)"
    for l in texto.splitlines():
        if l.startswith("## "):
            clave = l[3:]
            out[clave] = []
        out[clave].append(l)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--antes", type=Path, required=True)
    ap.add_argument("--despues", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    a = ap.parse_args()
    ta, td = a.antes.read_text(encoding="utf-8"), a.despues.read_text(encoding="utf-8")
    sa, sd = secciones(ta), secciones(td)
    out = [f"Comparación del README: antes {len(ta.splitlines())} líneas, ahora {len(td.splitlines())} líneas.", ""]
    for k in list(dict.fromkeys(list(sa) + list(sd))):
        antes, desp = sa.get(k), sd.get(k)
        if antes is None:
            out.append(f"[NUEVA] {k}: {len(desp)} líneas.")
            continue
        if desp is None:
            out.append(f"[QUITADA] {k}")
            continue
        sm = difflib.SequenceMatcher(a=antes, b=desp, autojunk=False)
        agregadas = sum(j2 - j1 for op, i1, i2, j1, j2 in sm.get_opcodes() if op in ("insert", "replace"))
        quitadas = sum(i2 - i1 for op, i1, i2, j1, j2 in sm.get_opcodes() if op in ("delete", "replace"))
        out.append(f"{k}: {len(antes)} -> {len(desp)} líneas; {agregadas} agregadas o cambiadas, {quitadas} quitadas o cambiadas.")
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            for l in antes[i1:i2]:
                if l.strip():
                    out.append("    - " + l[:150])
            for l in desp[j1:j2]:
                if l.strip():
                    out.append("    + " + l[:150])
    nums_a, nums_d = set(NUM.findall(ta)), set(NUM.findall(td))
    falt = sorted(nums_a - nums_d)
    out += ["", f"CIFRAS: {len(nums_a)} distintas antes, {len(nums_d)} ahora; antes y ausentes ahora: {len(falt)}"]
    out += ["    " + ", ".join(falt[:120]) + (" ..." if len(falt) > 120 else "")] if falt else ["    ninguna: todas las cifras de antes siguen en el README."]
    adv_a = sum(len(ADV.findall(l)) for l in ta.splitlines())
    adv_d = sum(len(ADV.findall(l)) for l in td.splitlines())
    out += ["", f"ADVERTENCIAS (post hoc, sin validación con datos nuevos, en muestra, supuesto): {adv_a} menciones antes, {adv_d} ahora."]
    for frase in ("post hoc, no pre-declarado", "Siempre con una persona que revisa y decide", "no está en git", "licencia no comercial"):
        out.append(f"    «{frase}»: antes {ta.count(frase)}, ahora {td.count(frase)}")
    a.salida.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"escrito {a.salida} ({len(out)} líneas); cifras ausentes: {len(falt)}")


if __name__ == "__main__":
    main()
