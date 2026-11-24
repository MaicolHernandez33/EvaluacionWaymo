"""F26: genera el favicon de la página (``app/assets/icono.png``, 256 x 256) con el MISMO símbolo del wordmark (``estilos.simbolo_interior``): un cuadro redondeado en panel alto con un mini anillo de
cinco cuñas en acento alrededor de la silueta de un auto visto desde arriba. Usa solo Pillow (ya instalado), con sobremuestreo de 4x, y escribe además ``images/ep3/pagina/f26_favicon_16.png``
(el mismo icono a 16 px, ampliado 8 veces con vecinos más cercanos) para comprobar que se lee a 16 px.
Uso: .venv\Scripts\python scripts/ep3/generar_icono.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
import estilos as E  # noqa: E402

SALIDA = RAIZ / "app/assets/icono.png"
SALIDA_16 = RAIZ / "images/ep3/pagina/f26_favicon_16.png"


def dibujar(lado: int = 256, sobremuestreo: int = 4) -> Image.Image:
    t = E.TOKENS
    n = lado * sobremuestreo
    k = n / E.SIMBOLO_LADO
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0.5 * k, 0.5 * k, 27.5 * k, 27.5 * k], radius=7 * k, fill=t["panel_alto"], outline=t["panel_alto_borde"], width=max(1, round(k)))
    for cuna in E.cunas_simbolo():
        d.polygon([(x * k, y * k) for x, y in cuna], fill=t["acento"])
    x, y, w, h, rx = E.SIMBOLO_AUTO
    d.rounded_rectangle([x * k, y * k, (x + w) * k, (y + h) * k], radius=rx * k, fill=t["texto"])
    d.line([((x + 1.1) * k, (y + 3.2) * k), ((x + w - 1.1) * k, (y + 3.2) * k)], fill=t["panel_alto"], width=max(1, round(k)))
    return img.resize((lado, lado), Image.LANCZOS)


def main() -> None:
    icono = dibujar(256)
    icono.save(SALIDA)
    chico = icono.resize((16, 16), Image.LANCZOS)
    fondo = Image.new("RGBA", (16, 16), E.TOKENS["fondo"])
    fondo.alpha_composite(chico)
    fondo.resize((128, 128), Image.NEAREST).save(SALIDA_16)
    print("escritos", SALIDA.relative_to(RAIZ), SALIDA_16.relative_to(RAIZ))


if __name__ == "__main__":
    main()
