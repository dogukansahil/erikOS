#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Remove temporary test trees inside the WSL build distro (run as root).
# Safe to run any time. Keeps the package cache
# (~/erik-work/cache), the built packages and /root/testroot.tar.
set -eu

for dir in /root/testroot /root/erik-work/audit-test /root/erik-work/audit /root/erik-work/src; do
    [ -e "$dir" ] || continue
    # never delete through a bind mount (/proc, /dev/pts of a test chroot)
    umount -R "$dir/proc" "$dir/dev/pts" 2>/dev/null || true
    if grep -q " $dir[/ ]" /proc/mounts; then
        echo "skipped $dir: something is still mounted inside it" >&2
        continue
    fi
    rm -rf "$dir"
    echo "removed $dir"
done
apt-get clean
fstrim -av >/dev/null 2>&1 || true
