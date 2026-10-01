# SPDX-License-Identifier: GPL-3.0-only
# Shared paths for Erik OS build scripts. Sourced, not executed.

PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
PACKAGES_DIR=$PROJECT_DIR/packages
ARCHIVE_CONF=$PROJECT_DIR/archive/conf

# Builds run on the Linux file system: /mnt/c is slow and loses file modes.
WORK_DIR=${ERIK_WORK_DIR:-$HOME/erik-work}

# Local only, never published: signing key and reprepro database.
SECRETS_DIR=$PROJECT_DIR/build-environment/secrets
export GNUPGHOME=$SECRETS_DIR/gnupg

DEB_OUT=$WORK_DIR/debs
# Generated, signed APT tree: published from here, never committed.
APT_OUT=$PROJECT_DIR/build-environment/archive-out/apt

die() { echo "error: $*" >&2; exit 1; }

# Windows editors may save CRLF line endings, which break shell scripts
# and debian/ files. Refuse to build instead of producing a broken package.
check_line_endings() {
    bad=$(grep -rlI "$(printf '\r')" "$@" 2>/dev/null || true)
    [ -z "$bad" ] || die "CRLF line endings in: $bad"
}
