#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Enforce the Erik OS license policy (docs/LICENSING.md).

Fails the build when:
  * an Erik package declares any license other than GPL-3.0-only,
  * an Erik source file lacks the GPL-3.0-only SPDX header,
  * an edition enables any Debian archive area other than "main",
  * an edition's package lists name a package from the deny list.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LICENSE = "GPL-3.0-only"
SPDX = f"SPDX-License-Identifier: {LICENSE}"

# Files that cannot carry a comment header or are covered by debian/copyright.
NO_HEADER_NAMES = {"changelog", "format", "install", "links", "control", "copyright",
                   "os-release", "gnome-initial-setup-done", "erik-logo.txt", "erik-logo-fastfetch.txt", "options", "distributions"}
NO_HEADER_SUFFIXES = {".jpg", ".png", ".gpg", ".md", ".qml", ".desc", ".gen", ".list",
                      ".chroot", ".desktop"}

# Known non-free or redistribution-restricted software. Debian "main" already
# excludes these; the list catches anything added by hand or by a third-party
# source in the future.
DENY = re.compile(r"^(nvidia-|cuda|libcuda|firmware-(?!linux-free)|intel-microcode|"
                  r"amd64-microcode|steam|google-chrome|microsoft-|skype|zoom|"
                  r"virtualbox|unrar(?!-free)|rar$|ttf-mscorefonts)")


def check_copyright(path: Path, errors: list[str]) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("License:"):
            value = line.split(":", 1)[1].strip()
            if value != LICENSE:
                errors.append(f"{path.relative_to(ROOT)}: license '{value}' is not {LICENSE}")


def needs_header(path: Path) -> bool:
    if path.name in NO_HEADER_NAMES or path.suffix in NO_HEADER_SUFFIXES:
        return False
    return path.is_file()


def check_sources(errors: list[str]) -> None:
    packages = ROOT / "packages"
    for pkg in sorted(p for p in packages.iterdir() if p.is_dir()):
        copyright_file = pkg / "debian" / "copyright"
        if not copyright_file.is_file():
            errors.append(f"{pkg.relative_to(ROOT)}: missing debian/copyright")
            continue
        check_copyright(copyright_file, errors)
        for path in pkg.rglob("*"):
            if needs_header(path) and SPDX not in path.read_text(encoding="utf-8", errors="ignore"):
                errors.append(f"{path.relative_to(ROOT)}: missing '{SPDX}'")
    for script in sorted((ROOT / "scripts").rglob("*.sh")):
        if SPDX not in script.read_text(encoding="utf-8"):
            errors.append(f"{script.relative_to(ROOT)}: missing '{SPDX}'")


def check_editions(errors: list[str]) -> None:
    for config in sorted((ROOT / "editions").glob("*/auto/config")):
        text = config.read_text(encoding="utf-8")
        match = re.search(r'--archive-areas\s+"([^"]+)"', text)
        if not match or match.group(1).split() != ["main"]:
            errors.append(f"{config.relative_to(ROOT)}: --archive-areas must be exactly \"main\"")
    for listing in sorted((ROOT / "editions").glob("*/config/package-lists/*.list.chroot")):
        for word in listing.read_text(encoding="utf-8").split():
            if not word.startswith("#") and DENY.match(word):
                errors.append(f"{listing.relative_to(ROOT)}: '{word}' is not allowed")


def main() -> int:
    errors: list[str] = []
    check_sources(errors)
    check_editions(errors)
    if errors:
        print("License policy violations:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    print(f"License policy OK: Erik sources are {LICENSE}, Debian areas are main only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
