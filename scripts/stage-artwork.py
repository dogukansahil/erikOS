#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Copy the Erik logo from erik-theme into places a package cannot reach.

The erik-theme package is the single source of Erik artwork. Installed
systems get the logo and wallpapers from that package. Only the Calamares
branding on the desktop ISO needs its own copy, because the installer
branding is part of the live image, not of an installed package.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGO_SOURCE = ROOT / "packages" / "erik-theme" / "artwork" / "logo.png"
LOGO_DESTINATIONS = (
    ROOT / "editions" / "desktop" / "config" / "includes.chroot" / "etc" / "calamares"
    / "branding" / "erik" / "logo.png",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if a copy differs from the source")
    args = parser.parse_args()

    if not LOGO_SOURCE.is_file():
        print(f"Missing artwork source: {LOGO_SOURCE}", file=sys.stderr)
        return 1
    source = LOGO_SOURCE.read_bytes()

    if args.check:
        stale = [p for p in LOGO_DESTINATIONS if not p.is_file() or p.read_bytes() != source]
        for path in stale:
            print(f"Stale or missing: {path.relative_to(ROOT)}", file=sys.stderr)
        if not stale:
            print("Staged artwork is current.")
        return 1 if stale else 0

    for path in LOGO_DESTINATIONS:
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(LOGO_SOURCE, path)
        print(f"Staged {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
