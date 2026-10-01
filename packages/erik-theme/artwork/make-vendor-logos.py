#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Generate artwork/vendor-logos/ from artwork/logo.png.

The images replace Debian's logo wherever GNOME and other programs show the
vendor logo (for example the GDM login screen), through the vendor-logos
alternative that erik-theme registers. Run once after the logo changes and
commit the output; the package build does not run it.

Needs python3-pil and fonts-cantarell (both Debian main). Cantarell is
licensed under the SIL Open Font License, which allows its use in images.
"""

import base64
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
LOGO = HERE / "logo.png"
OUT = HERE / "vendor-logos"
FONT = "/usr/share/fonts/opentype/cantarell/Cantarell-VF.otf"   # variable font
TEXT = "Erik OS"
INK = (255, 255, 255, 255)   # login screens are dark


def logo(size):
    return Image.open(LOGO).convert("RGBA").resize((size, size), Image.LANCZOS)


def logo_with_text(height):
    mark = logo(height)
    font = ImageFont.truetype(FONT, int(height * 0.62))
    font.set_variation_by_name("Bold")
    left, top, right, bottom = font.getbbox(TEXT)
    gap = int(height * 0.18)
    canvas = Image.new("RGBA", (height + gap + right - left, height), (0, 0, 0, 0))
    canvas.alpha_composite(mark, (0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.text((height + gap - left, (height - (bottom - top)) // 2 - top), TEXT, font=font, fill=INK)
    return canvas


def svg_for(png_path):
    image = Image.open(png_path)
    data = base64.b64encode(png_path.read_bytes()).decode()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{image.width}" height="{image.height}">'
            f'<!-- SPDX-License-Identifier: GPL-3.0-only -->'
            f'<image width="{image.width}" height="{image.height}" href="data:image/png;base64,{data}"/></svg>\n')


def main():
    OUT.mkdir(exist_ok=True)
    for size in (64, 128, 256):
        logo(size).save(OUT / f"logo-{size}.png", optimize=True)
        text = logo_with_text(size)
        text.save(OUT / f"logo-text-{size}.png", optimize=True)
        # Debian adds the release number here; Erik shows the name only, so
        # the login screen does not need new artwork for every release.
        text.save(OUT / f"logo-text-version-{size}.png", optimize=True)
    for name in ("logo", "logo-text", "logo-text-version"):
        (OUT / f"{name}.svg").write_text(svg_for(OUT / f"{name}-256.png"))
    print(f"wrote {len(list(OUT.iterdir()))} files to {OUT}")


if __name__ == "__main__":
    main()
