#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Check what git would commit, before it is committed.

    python3 scripts/check-repo.py

Looks at every file git tracks or would add (tracked plus untracked, minus
.gitignore) and fails on:
  * files that must never be in the repository (build environment, signing
    keys, ISOs, virtual disks, generated APT trees),
  * private key blocks,
  * strings that identify the build machine: the generic ones below plus the
    personal ones listed outside git in build-environment/leak-strings.txt
    (the public maintainer address is allowed),
  * files larger than 20 MB,
  * CRLF line endings in text files.

Run it before every commit; CI runs it too (without the local strings).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 20 * 1024 * 1024
# Public on purpose: maintainer address and the photographer credit of the wallpapers.
PUBLIC_STRINGS = ["dogukansahil@gmail.com", "500px.com/p/dogukansahil"]

FORBIDDEN = re.compile(
    r"(^|/)(build-environment|releases|archive-out)/|\.(iso|img|vdi|vmdk|vhdx|qcow2|sav)$"
    r"|(^|/)(secring\.gpg|private-keys-v1\.d|pubring\.kbx|trustdb\.gpg|id_rsa|id_ed25519)$"
    r"|(^|/)\.env$")
GENERIC_LEAKS = ["/mnt/c/Users/", "C:\\Users\\", "C:/Users/"]
KEY_HEADER = re.compile(rb"-----BEGIN ((?:[A-Z]+ )?PRIVATE KEY|PGP PRIVATE KEY BLOCK)-----")
KEY_BODY = re.compile(rb"[A-Za-z0-9+/=:,.()\s-]*")
BINARY_SUFFIXES = {".jpg", ".jpeg", ".png", ".gpg", ".svg", ".ico", ".pdf"}

# Files that name the generic strings on purpose (scanners and their tests).
LEAK_SCANNERS = {"scripts/audit-iso.py", "scripts/check-repo.py", "scripts/tests/test-audit-iso.sh",
                 "scripts/new-pc.ps1", "scripts/try-iso.ps1",
                 "scripts/cleanup-wsl.sh"}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True,
                          capture_output=True).stdout


def candidate_files() -> list[str]:
    out = git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    return sorted(p for p in out.split("\0") if p)


def local_leaks() -> list[str]:
    path = ROOT / "build-environment" / "leak-strings.txt"
    if not path.is_file():
        return []
    return [s.strip() for s in path.read_text().splitlines() if s.strip() and not s.startswith("#")]


def has_key_block(data: bytes) -> bool:
    for match in KEY_HEADER.finditer(data):
        footer = b"-----END " + match.group(1) + b"-----"
        end = data.find(footer, match.end(), match.end() + 65536)
        body = data[match.end():end] if end >= 0 else b""
        if end >= 0 and KEY_BODY.fullmatch(body) and len(re.sub(rb"\s", b"", body)) >= 40:
            return True
    return False


def main() -> int:
    personal = local_leaks()
    problems: list[str] = []
    files = candidate_files()
    for rel in files:
        path = ROOT / rel
        if FORBIDDEN.search(rel) and rel != "build-environment/README.md":
            problems.append(f"{rel}: must never be committed")
            continue
        if not path.is_file():
            continue
        size = path.stat().st_size
        if size > MAX_BYTES:
            problems.append(f"{rel}: {size / 1048576:.1f} MB, over the 20 MB limit")
        data = path.read_bytes()
        if has_key_block(data):
            problems.append(f"{rel}: contains a private key")
        if path.suffix.lower() in BINARY_SUFFIXES or b"\0" in data[:8192]:
            continue
        text = data.decode("utf-8", errors="replace")
        if "\r\n" in text:
            problems.append(f"{rel}: CRLF line endings")
        scrubbed = text
        for public in PUBLIC_STRINGS:
            scrubbed = scrubbed.replace(public, "")
        for s in personal:
            if s.lower() in scrubbed.lower():
                problems.append(f"{rel}: contains a personal build machine string")
                break
        if rel not in LEAK_SCANNERS:
            for s in GENERIC_LEAKS:
                if s in text:
                    problems.append(f"{rel}: contains '{s}' (local path or build host)")
                    break
    if problems:
        print("Repository check failed:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    note = "" if personal else " (no build-environment/leak-strings.txt: personal strings not checked)"
    print(f"Repository check OK: {len(files)} files{note}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
