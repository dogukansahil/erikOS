#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Build every Erik package under packages/ (or the ones named) and
# check it with lintian and the Erik license check.
# Usage: sh scripts/build-packages.sh [package ...]
set -eu
. "$(dirname "$0")/common.sh"

cd "$PACKAGES_DIR"
packages=${*:-$(ls -d erik-*/ | tr -d /)}

python3 "$PROJECT_DIR/scripts/check-licenses.py"
mkdir -p "$WORK_DIR/src" "$DEB_OUT"

for pkg in $packages; do
    [ -d "$pkg/debian" ] || die "$pkg is not a package directory"
    check_line_endings "$pkg"
    echo "==> $pkg"
    rm -rf "$WORK_DIR/src/$pkg"
    rm -f "$DEB_OUT/${pkg}_"*
    cp -r "$pkg" "$WORK_DIR/src/$pkg"
    # Files from /mnt/c all look executable. Only scripts may keep the bit,
    # or debhelper treats config files such as debian/install as programs.
    find "$WORK_DIR/src/$pkg" -type d -exec chmod 0755 {} +
    find "$WORK_DIR/src/$pkg" -type f -exec chmod 0644 {} +
    find "$WORK_DIR/src/$pkg" -type f -exec sh -c \
        'for f; do [ "$(head -c 2 "$f")" = "#!" ] && chmod 0755 "$f"; done; true' sh {} +
    (cd "$WORK_DIR/src/$pkg" && dpkg-buildpackage --no-sign -us -uc)
    mv "$WORK_DIR/src/${pkg}_"* "$DEB_OUT/"
    lintian --fail-on error --suppress-tags no-manual-page,initial-upload-closes-no-bugs \
        "$DEB_OUT/${pkg}_"*.changes
done

echo "Packages are in $DEB_OUT"
