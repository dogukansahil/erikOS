#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Create the Erik repository signing key once, and export its public half
# into the erik-archive-keyring package. The private key stays in
# build-environment/secrets and must never be committed or published.
set -eu
. "$(dirname "$0")/common.sh"

mkdir -p "$GNUPGHOME"
chmod 0700 "$SECRETS_DIR" "$GNUPGHOME"

if ! gpg --batch --list-secret-keys "Erik OS Archive" >/dev/null 2>&1; then
    gpg --batch --pinentry-mode loopback --passphrase '' \
        --quick-generate-key "Erik OS Archive Signing Key <dogukansahil@gmail.com>" \
        ed25519 sign 3y
fi

out=$PACKAGES_DIR/erik-archive-keyring/keyrings
mkdir -p "$out"
gpg --batch --export "Erik OS Archive" > "$out/erik-archive-keyring.gpg"
gpg --batch --list-keys --with-fingerprint "Erik OS Archive"
echo "Public key exported to $out/erik-archive-keyring.gpg"
