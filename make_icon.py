#!/usr/bin/env python3
"""
FieldLog — Icon Generator
Creates assets/icon.png (256×256) using Pillow.
Run once, or it is called automatically by install.py.
"""
from pathlib import Path

HERE       = Path(__file__).parent
ICON_PNG   = HERE / "assets" / "icon.png"

BLUE       = (37,  99, 235, 255)   # #2563eb
WHITE      = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)


def generate(size: int = 256) -> Path:
    from PIL import Image, ImageDraw

    ICON_PNG.parent.mkdir(parents=True, exist_ok=True)

    img  = Image.new("RGBA", (size, size), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    # Blue rounded-rectangle background
    margin = round(size * 0.05)
    radius = round(size * 0.18)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=BLUE,
    )

    # White form bars (representing a data entry form)
    bar_x1   = round(size * 0.21)
    bar_x2   = round(size * 0.79)
    bar_h    = round(size * 0.055)
    bar_r    = round(bar_h * 0.4)
    short_x2 = round(size * 0.58)
    centers  = [
        round(size * 0.36),
        round(size * 0.49),
        round(size * 0.62),
        round(size * 0.73),
    ]
    for i, cy in enumerate(centers):
        x2 = short_x2 if i == len(centers) - 1 else bar_x2
        draw.rounded_rectangle(
            [bar_x1, cy - bar_h // 2, x2, cy + bar_h // 2],
            radius=bar_r,
            fill=WHITE,
        )

    img.save(ICON_PNG)
    return ICON_PNG


if __name__ == "__main__":
    path = generate()
    print(f"✓ Icon saved → {path}")
