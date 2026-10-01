#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Prove that scripts/audit-iso.py catches what it promises to catch.
# Takes a real Erik ISO, plants one problem of every kind into a copy,
# repacks it and expects the audit to FAIL with each problem named.
# Usage (root, WSL): sh scripts/tests/test-audit-iso.sh releases/0.3/erikos-0.3-server-amd64.iso
set -eu

iso=$(realpath "$1")
PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
T=${ERIK_WORK_DIR:-$HOME/erik-work}/audit-test
rm -rf "$T"; mkdir -p "$T/iso/live"

xorriso -osirrox on -indev "$iso" -extract /live/filesystem.squashfs "$T/fs.squashfs" >/dev/null 2>&1
unsquashfs -no-progress -d "$T/root" "$T/fs.squashfs" >/dev/null
R=$T/root

# 1 private key generated during the build (would be shared by every install)
{ echo '-----BEGIN OPENSSH PRIVATE KEY-----'; head -c 300 /dev/urandom | base64 -w 70; echo '-----END OPENSSH PRIVATE KEY-----'; } > "$R/etc/ssh/ssh_host_ed25519_key"
# 2 shell history of the builder
echo 'sudo lb build' > "$R/root/.bash_history"
# 3 Windows path of the build machine
echo 'C:\Users\builder\Desktop' > "$R/opt/leak.txt"
# 4 a Debian package file edited in place
echo '# tampered' >> "$R/usr/bin/which.debianutils"
# 5 a copy of a local secret (repository signing key ring)
cp "$PROJECT_DIR/build-environment/secrets/gnupg/pubring.kbx" "$R/opt/keyring.kbx"
# 6 a user with a password hash
echo 'builder:$6$salt$hash:20000:0:99999:7:::' >> "$R/etc/shadow"
echo 'builder:x:1000:1000::/home/builder:/bin/sh' >> "$R/etc/passwd"
# 7 the local build repository left in APT sources
echo 'deb [trusted=yes] file:/root/packages ./' > "$R/etc/apt/sources.list.d/build.list"
# 8 an unexpected file on the ISO next to the live system
echo 'notes' > "$T/iso/notes.txt"

mksquashfs "$R" "$T/iso/live/filesystem.squashfs" -comp zstd -noappend -quiet >/dev/null
xorriso -as mkisofs -quiet -o "$T/erikos-test-server-amd64.iso" "$T/iso" 2>/dev/null

set +e
python3 "$PROJECT_DIR/scripts/audit-iso.py" --edition server "$T/erikos-test-server-amd64.iso" >/dev/null 2>&1
code=$?
set -e
report=$T/erikos-test-server-amd64.iso.audit.txt

fail=0
expect() {
    if grep -q -- "$2" "$report"; then echo "  caught  $1"; else echo "  MISSED  $1"; fail=1; fi
}
echo "audit exit code: $code (expected 1)"
[ "$code" -eq 1 ] || fail=1
expect "generated private key"      "private key in the image: /etc/ssh/ssh_host_ed25519_key"
expect "shell history"              "credential file name in the image: /root/.bash_history"
expect "Windows path / user name"   "build machine string (user, host, path or password) in: /opt/leak.txt"
expect "edited Debian file"         "package file was modified after install: /usr/bin/which.debianutils"
expect "copy of a local secret"     "/opt/keyring.kbx is identical to local secret"
expect "password hash"              "account builder has a set password"
expect "regular user"               "regular user builder exists"
expect "build APT repository"       "unexpected APT source in /etc/apt/sources.list.d/build.list"
expect "unowned file"               "not allowlisted: /opt/leak.txt"
expect "unexpected ISO file"        "outside the root file system: /notes.txt"

rm -rf "$T/root" "$T/iso" "$T/fs.squashfs"
[ "$fail" -eq 0 ] && echo "PASS: the audit caught every planted problem" || { echo "FAIL: the audit missed something"; exit 1; }
