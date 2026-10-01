#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Generate the Erik ASCII logo from artwork/logo.png.

One logo for every text surface: fastfetch, the server login banner,
documentation. Written to the erik-base package (both editions use it):

  erik-base/files/erik-logo.txt            plain text
  erik-base/files/erik-logo-fastfetch.txt  same, with fastfetch colour mark

Run after the logo changes and commit the output; the package build does
not run it. Needs python3-pil.
"""

from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
LOGO = HERE / "logo.png"
OUT = HERE.parents[1] / "erik-base" / "files"
WIDTH = 30            # columns
CELL_ASPECT = 2.1     # a terminal cell is about twice as tall as it is wide
# Coverage of a cell by the logo -> character, light to full.
RAMP = " .:-=+*%#"


def render() -> list[str]:
    image = Image.open(LOGO).convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    image = image.crop(bbox)
    height = max(1, round(WIDTH * image.height / image.width / CELL_ASPECT))
    # Oversample, then average each cell: smoother edges than a plain resize.
    sx, sy = 8, 16
    alpha = image.getchannel("A").resize((WIDTH * sx, height * sy), Image.LANCZOS)
    px = alpha.load()
    lines = []
    for row in range(height):
        chars = []
        for col in range(WIDTH):
            total = sum(px[col * sx + x, row * sy + y] for x in range(sx) for y in range(sy))
            coverage = total / (sx * sy * 255)
            chars.append(RAMP[min(len(RAMP) - 1, round(coverage * (len(RAMP) - 1)))])
        lines.append("".join(chars).rstrip())
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def main():
    lines = render()
    text = "\n".join(lines) + "\n"
    (OUT / "erik-logo.txt").write_text(text)
    # fastfetch replaces $1 with logo colour 1 (set in the fastfetch config).
    (OUT / "erik-logo-fastfetch.txt").write_text("$1" + text)
    print(text)


if __name__ == "__main__":
    main()
