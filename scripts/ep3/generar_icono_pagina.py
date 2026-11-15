"""F18-C1: genera app/assets/icono.png (icono de la pagina, propio, sin marcas ni logos de terceros). Dibujo con Pillow: caja 3D con una marca de verificacion."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "app" / "assets" / "icono.png"
AZUL, BLANCO, ACENTO = (29, 78, 137), (255, 255, 255), (11, 110, 105)


def main() -> None:
    n = 256
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([8, 8, n - 8, n - 8], radius=48, fill=AZUL)
    # cubo en perspectiva (la «caja 3D»)
    f = [(70, 110), (150, 110), (150, 190), (70, 190)]
    b = [(100, 80), (180, 80), (180, 160), (100, 160)]
    for p, q in zip(f, f[1:] + f[:1]):
        d.line([p, q], fill=BLANCO, width=9)
    for p, q in zip(b, b[1:] + b[:1]):
        d.line([p, q], fill=BLANCO, width=9)
    for p, q in zip(f, b):
        d.line([p, q], fill=BLANCO, width=9)
    # marca de verificacion (una persona revisa)
    d.ellipse([140, 140, 236, 236], fill=ACENTO, outline=BLANCO, width=7)
    d.line([(163, 190), (184, 211), (218, 168)], fill=BLANCO, width=12, joint="curve")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    im.save(SALIDA)
    print("icono escrito:", SALIDA, im.size)


if __name__ == "__main__":
    main()
