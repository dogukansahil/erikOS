#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Add built packages to the signed APT tree in build-environment/archive-out/apt.
# Usage: sh scripts/publish-repo.sh [stable|testing]
# New packages go to testing first; promote to stable after testing.
set -eu
. "$(dirname "$0")/common.sh"

suite=${1:-testing}
case "$suite" in stable|testing) ;; *) die "suite must be stable or testing" ;; esac

db=$SECRETS_DIR/reprepro
mkdir -p "$db" "$APT_OUT"
rr() { reprepro --basedir "$db" --confdir "$ARCHIVE_CONF" --outdir "$APT_OUT" "$@"; }

for dsc in "$DEB_OUT"/*.dsc; do
    rr includedsc "$suite" "$dsc"
done
for deb in "$DEB_OUT"/*.deb; do
    rr includedeb "$suite" "$deb"
done

rr export "$suite"
cp "$PACKAGES_DIR/erik-archive-keyring/keyrings/erik-archive-keyring.gpg" "$APT_OUT/"
rr list "$suite"
