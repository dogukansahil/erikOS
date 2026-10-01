#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Audit an Erik OS ISO before release: nothing ships that should not.

Run as root in the WSL build distro:
    python3 scripts/audit-iso.py releases/0.3/erikos-0.3-desktop-amd64.iso

The ISO itself is opened (not the build tree), so the audit sees exactly what
users download. Checks:

  packages   every installed package is the exact version published in
             Debian trixie "main" (index signatures verified with the Debian
             archive keyring) or an Erik package built locally
  files      every file belongs to a package, or is an expected generated
             file listed in scripts/audit-allowlist.conf, or comes from the
             edition's includes.chroot
  secrets    no private keys outside Debian package files, no file identical
             to anything in build-environment/secrets or the old VM media,
             no builder password, no Windows paths, user or host names
  accounts   no account with a password hash, no users in /home
  leftovers  no build repositories in APT sources, no cached .deb files
  iso        only expected files outside the root file system

Writes <iso>.manifest (package, version, origin) and <iso>.audit.txt next to
the ISO. Exit code 0 = PASS, 1 = FAIL, 2 = could not run.
"""

from __future__ import annotations

import argparse
import hashlib
import lzma
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("ERIK_WORK_DIR", Path.home() / "erik-work"))
DEB_OUT = WORK / "debs"
KEYRING = "/usr/share/keyrings/debian-archive-keyring.pgp"

DEBIAN_INDEXES = (
    ("https://deb.debian.org/debian", "trixie"),
    ("https://deb.debian.org/debian", "trixie-updates"),
    ("https://security.debian.org/debian-security", "trixie-security"),
)

# Strings that identify the build machine. Never allowed, except the
# maintainer address in package metadata and Erik package files. Personal
# values (user name, host name) live outside git, one per line, in
# build-environment/leak-strings.txt.
LEAK_SPECIFIC = ["erik-work", "build-environment", "ErikOS-Build"]
_LOCAL_LEAKS = ROOT / "build-environment" / "leak-strings.txt"
if _LOCAL_LEAKS.is_file():
    LEAK_SPECIFIC += [s.strip() for s in _LOCAL_LEAKS.read_text().splitlines()
                      if s.strip() and not s.startswith("#")]# Generic Windows/WSL paths. Unchanged Debian files may contain them as
# examples (LibreOffice help), so they only count outside verified files.
LEAK_GENERIC = ("/mnt/c/", "C:\\Users", "C:/Users")
# Files where the maintainer address legitimately appears.
LEAK_ALLOWED = re.compile(r"^/var/lib/dpkg/(status|status-old|available)$")

PRIVATE_KEY = rb"-----BEGIN ([A-Z]+ )?PRIVATE KEY-----|-----BEGIN PGP PRIVATE KEY BLOCK-----"
# A real key is a whole block: header, base64 body, matching footer. Programs
# (ssh, gnutls) and the MIME database contain the header text alone.
KEY_HEADER = re.compile(rb"-----BEGIN ((?:[A-Z]+ )?PRIVATE KEY|PGP PRIVATE KEY BLOCK)-----")
KEY_BODY = re.compile(rb"[A-Za-z0-9+/=:,.()\s-]*")


def has_key_block(data: bytes) -> bool:
    """True if data holds a complete PEM/PGP private key block (linear time)."""
    for match in KEY_HEADER.finditer(data):
        footer = b"-----END " + match.group(1) + b"-----"
        end = data.find(footer, match.end(), match.end() + 65536)
        if end < 0:
            continue
        body = data[match.end():end]
        if KEY_BODY.fullmatch(body) and len(re.sub(rb"\s", b"", body)) >= 40:
            return True
    return False
SECRET_NAMES = re.compile(r"(^|/)(id_rsa|id_ed25519|id_ecdsa|\.bash_history|\.netrc|\.git-credentials"
                          r"|private-keys-v1\.d|secring\.gpg|\.env)(/|$)")

ISO_ALLOWED = re.compile(
    r"^/(boot/|EFI/|live/(vmlinuz|initrd|filesystem\.)|\.disk/|md5sum\.txt$|sha256sum\.txt$"
    r"|(md5|sha256)sum\.README$|efi\.img$|install/|pool/|pool-udeb/|dists/|isolinux/|tools/|firmware/)")


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.failures = 0

    @property
    def failed(self) -> bool:
        return self.failures > 0

    def section(self, title: str) -> None:
        self.lines.append(f"\n== {title}")
        print(f"== {title}", flush=True)

    def ok(self, msg: str) -> None:
        self.lines.append(f"  ok    {msg}")

    def info(self, msg: str) -> None:
        self.lines.append(f"  info  {msg}")

    def fail(self, msg: str) -> None:
        self.failures += 1
        self.lines.append(f"  FAIL  {msg}")
        print(f"  FAIL  {msg}", flush=True)


def run(*cmd: str, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw)


# ---------------------------------------------------------------- extraction

def extract(iso: Path, dest: Path) -> tuple[Path, list[str]]:
    listing = run("xorriso", "-indev", str(iso), "-find", "/", "-type", "f").stdout
    iso_files = [line.strip().strip("'") for line in listing.splitlines() if line.startswith("'")]
    squash = dest / "filesystem.squashfs"
    run("xorriso", "-osirrox", "on", "-indev", str(iso),
        "-extract", "/live/filesystem.squashfs", str(squash))
    rootfs = dest / "root"
    run("unsquashfs", "-no-progress", "-d", str(rootfs), str(squash))
    squash.unlink()
    return rootfs, iso_files


# ------------------------------------------------------------------ packages

def parse_stanzas(text: str):
    for block in text.split("\n\n"):
        fields: dict[str, str] = {}
        key = None
        for line in block.splitlines():
            if line[:1] in (" ", "\t") and key:
                fields[key] += "\n" + line
            elif ":" in line:
                key, value = line.split(":", 1)
                fields[key] = value.strip()
        if fields:
            yield fields


def debian_index(cache: Path) -> dict[tuple[str, str], str]:
    """(package, version) -> suite, for Debian main, signature verified."""
    allowed: dict[tuple[str, str], str] = {}
    cache.mkdir(parents=True, exist_ok=True)
    for base, suite in DEBIAN_INDEXES:
        inrelease = cache / f"{suite}.InRelease"
        urllib.request.urlretrieve(f"{base}/dists/{suite}/InRelease", inrelease)
        verified = cache / f"{suite}.Release"
        run("gpgv", "--keyring", KEYRING, "--output", str(verified), str(inrelease))
        release = verified.read_text()
        name = "main/binary-amd64/Packages.xz"
        match = re.search(r"^ ([0-9a-f]{64})\s+\d+\s+" + re.escape(name) + "$", release, re.M)
        if not match:
            raise RuntimeError(f"{suite}: {name} not listed in signed Release")
        data = urllib.request.urlopen(f"{base}/dists/{suite}/{name}").read()
        if hashlib.sha256(data).hexdigest() != match.group(1):
            raise RuntimeError(f"{suite}: {name} does not match the signed Release")
        for st in parse_stanzas(lzma.decompress(data).decode()):
            allowed.setdefault((st["Package"], st["Version"]), suite)
    return allowed


def erik_index() -> dict[tuple[str, str], str]:
    """Erik packages: the current build output and every published version."""
    built: dict[tuple[str, str], str] = {}
    pool = ROOT / "build-environment" / "archive-out" / "apt" / "pool"
    for deb in [*DEB_OUT.glob("erik-*_all.deb"), *pool.rglob("erik-*_all.deb")]:
        name, version = run("dpkg-deb", "-f", str(deb), "Package", "Version").stdout.split("\n")[:2]
        built[(name.split(": ", 1)[1], version.split(": ", 1)[1])] = "erik"
    return built


def check_packages(rootfs: Path, rep: Report, cache: Path, manifest: Path) -> dict[str, str]:
    rep.section("packages")
    before = rep.failures
    installed = []
    for st in parse_stanzas((rootfs / "var/lib/dpkg/status").read_text()):
        if st.get("Status", "").endswith(" installed"):
            installed.append((st["Package"], st["Version"], st.get("Architecture", "")))
    origins = debian_index(cache)
    origins.update(erik_index())
    lines = []
    for name, version, arch in sorted(installed):
        origin = origins.get((name, version))
        if origin is None:
            rep.fail(f"{name} {version}: not in Debian trixie main and not a built Erik package")
            origin = "UNKNOWN"
        lines.append(f"{name}\t{version}\t{arch}\t{origin}")
    manifest.write_text("# package\tversion\tarchitecture\torigin\n" + "\n".join(lines) + "\n")
    erik = [n for n, _, _ in installed if n.startswith("erik-")]
    if rep.failures == before:
        rep.ok(f"{len(installed)} packages, all from Debian main or Erik")
    rep.info("Erik packages: " + ", ".join(sorted(erik)))
    return {n: v for n, v, _ in installed}


# ----------------------------------------------------------------- integrity

def check_integrity(rootfs: Path, rep: Report, modified_ok: list[re.Pattern]) -> set[str]:
    """Compare every package file with the md5sum dpkg recorded at install.

    A changed Debian file means a hook edited another package's file, which
    the next apt upgrade silently undoes. Returns the paths that verified.
    """
    rep.section("integrity")
    before = rep.failures
    info = rootfs / "var/lib/dpkg/info"
    entries: list[tuple[str, str, str]] = []          # (path, md5, package)
    for sums in info.glob("*.md5sums"):
        pkg = sums.stem.split(":")[0]
        for line in sums.read_text(errors="replace").splitlines():
            digest, _, rel = line.partition("  ")
            if rel:
                entries.append(("/" + rel, digest, pkg))
    for st in parse_stanzas((rootfs / "var/lib/dpkg/status").read_text()):
        for line in st.get("Conffiles", "").splitlines():
            parts = line.split()
            if len(parts) >= 2 and len(parts[1]) == 32:   # "obsolete" entries have no md5
                entries.append((parts[0], parts[1], st["Package"]))

    # dpkg-divert: the diverted package's file lives at the divert target.
    diversions: dict[str, tuple[str, str]] = {}
    div = rootfs / "var/lib/dpkg/diversions"
    if div.exists():
        lines = div.read_text().splitlines()
        for i in range(0, len(lines) - 2, 3):
            diversions[lines[i]] = (lines[i + 1], lines[i + 2])

    real_root = os.path.realpath(rootfs)
    verified: set[str] = set()
    missing = 0
    for path, digest, pkg in entries:
        if path in diversions and diversions[path][1] != pkg:
            path = diversions[path][0]
        candidates = [path]
        if re.match(r"^/(bin|sbin|lib|lib64)/", path):     # /usr-merge aliases
            candidates.append("/usr" + path)
        full = None
        for cand in candidates:
            f = os.path.join(real_root, cand.lstrip("/"))
            if os.path.realpath(f).startswith(real_root + "/") and os.path.isfile(f):
                full = f
                break
        if full is None:
            missing += 1
            continue
        if hashlib.md5(Path(full).read_bytes()).hexdigest() == digest:
            verified.add(path)
        elif any(p.search(path) for p in modified_ok):
            rep.info(f"modified on purpose (see allowlist): {path} [{pkg}]")
        else:
            rep.fail(f"package file was modified after install: {path} [{pkg}]")
    rep.info(f"{len(entries)} package files listed, {missing} not present (excluded docs, diverted)")
    if rep.failures == before:
        rep.ok(f"{len(verified)} package files are byte-identical to their Debian or Erik package")
    return verified


# --------------------------------------------------------------------- files

def owned_paths(rootfs: Path) -> tuple[set[str], dict[str, str]]:
    owned: set[str] = set()
    owner: dict[str, str] = {}
    for lst in (rootfs / "var/lib/dpkg/info").glob("*.list"):
        pkg = lst.stem.split(":")[0]
        for line in lst.read_text(errors="replace").splitlines():
            owned.add(line)
            owner.setdefault(line, pkg)
    div = (rootfs / "var/lib/dpkg/diversions")
    if div.exists():
        parts = div.read_text().splitlines()
        for i in range(0, len(parts) - 2, 3):
            owned.add(parts[i + 1])
            owner.setdefault(parts[i + 1], parts[i + 2])
    # /usr-merge: dpkg may record /bin/x while the file lives at /usr/bin/x.
    for path in list(owned):
        for alias in ("/bin", "/sbin", "/lib", "/lib64"):
            if path.startswith(alias + "/"):
                owned.add("/usr" + path)
                owner.setdefault("/usr" + path, owner[path])
    return owned, owner


def load_allowlist(edition: str) -> tuple[list[re.Pattern], list[re.Pattern]]:
    """(unowned files allowed, package files allowed to differ)."""
    patterns = []
    modified = []
    conf = ROOT / "scripts" / "audit-allowlist.conf"
    for line in conf.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line.startswith("modified "):
            modified.append(re.compile(line.split(None, 1)[1]))
        elif line:
            patterns.append(re.compile(line))
    for tree in ("common", edition):
        inc = ROOT / "editions" / tree / "config" / "includes.chroot"
        if inc.is_dir():
            for f in inc.rglob("*"):
                if f.is_file():
                    patterns.append(re.compile("^" + re.escape("/" + f.relative_to(inc).as_posix()) + "$"))
    return patterns, modified


def walk(rootfs: Path):
    for dirpath, dirnames, filenames in os.walk(rootfs):
        for name in filenames + [d for d in dirnames if os.path.islink(os.path.join(dirpath, d))]:
            full = os.path.join(dirpath, name)
            yield "/" + os.path.relpath(full, rootfs), full


def check_files(rootfs: Path, rep: Report, allow: list[re.Pattern], owned: set[str]) -> None:
    rep.section("files")
    unowned = []
    count = 0
    for path, full in walk(rootfs):
        count += 1
        if path in owned or any(p.search(path) for p in allow):
            continue
        if os.path.isdir(full) and not os.path.islink(full):
            continue
        # update-alternatives links (/usr/bin/vi -> /etc/alternatives/vi) are
        # created by maintainer scripts and point into the alternatives system.
        if os.path.islink(full) and os.readlink(full).startswith("/etc/alternatives/"):
            continue
        unowned.append(path)
    for path in unowned[:200]:
        rep.fail(f"file not from any package and not allowlisted: {path}")
    if len(unowned) > 200:
        rep.fail(f"... and {len(unowned) - 200} more")
    if not unowned:
        rep.ok(f"{count} files: every file is from a package or an expected generated file")


# ------------------------------------------------------------------- secrets

def secret_hashes(rep: Report) -> dict[tuple[int, str], str]:
    """sha256 of every small file we must never ship, keyed by (size, hash)."""
    known: dict[tuple[int, str], str] = {}
    for d in (ROOT / "build-environment" / "secrets", ROOT / "build-environment" / "work" / "vm-media"):
        if not d.is_dir():
            continue
        for f in d.rglob("*"):
            if f.is_file() and not f.is_symlink() and 0 < f.stat().st_size < 10 * 1024 * 1024:
                try:
                    digest = hashlib.sha256(f.read_bytes()).hexdigest()
                except PermissionError:
                    rep.info(f"could not read {f.relative_to(ROOT)} (Windows permissions), not compared")
                    continue
                known[(f.stat().st_size, digest)] = str(f.relative_to(ROOT))
    return known


def grep_files(rootfs: Path, args: list[str]) -> list[str]:
    # patterns go after -e or -f: a pattern starting with "-" is otherwise read as an option
    proc = subprocess.run(["grep", "-rlas", *args, "--", str(rootfs)], text=True, capture_output=True)
    if proc.returncode > 1:
        raise RuntimeError(f"grep failed: {proc.stderr.strip()}")
    return ["/" + os.path.relpath(p, rootfs) for p in proc.stdout.splitlines()]


def check_secrets(rootfs: Path, rep: Report, owner: dict[str, str], verified: set[str]) -> None:
    rep.section("secrets")
    before = rep.failures

    for path in grep_files(rootfs, ["-E", "-e", PRIVATE_KEY.decode()]):
        full = rootfs / path.lstrip("/")
        if not has_key_block(full.read_bytes()):
            rep.info(f"key header text without a key (program code, MIME rules): {path}")
            continue
        pkg = owner.get(path)
        if pkg and not pkg.startswith("erik-") and path in verified:
            rep.info(f"private key inside an unchanged Debian file (Debian test data): {path} [{pkg}]")
        else:
            rep.fail(f"private key in the image: {path}" + (f" [{pkg}]" if pkg else " (generated during build)"))

    for path, _ in walk(rootfs):
        if SECRET_NAMES.search(path):
            rep.fail(f"credential file name in the image: {path}")

    specific = list(LEAK_SPECIFIC)
    pw_file = ROOT / "build-environment" / "work" / "vm-media" / "erik-build-password.txt"
    try:
        pw = pw_file.read_text().strip()
        if len(pw) >= 6:
            specific.append(pw)
    except (FileNotFoundError, PermissionError):
        rep.info("builder password file not readable, not searched")
    for strings, generic in ((specific, False), (list(LEAK_GENERIC), True)):
        with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
            tmp.write("\n".join(strings) + "\n")
        hits = grep_files(rootfs, ["-F", "-f", tmp.name])
        os.unlink(tmp.name)
        for path in hits:
            pkg = owner.get(path, "")
            if pkg.startswith("erik-") or LEAK_ALLOWED.search(path):
                continue
            if generic and path in verified:
                continue
            rep.fail(f"build machine string (user, host, path or password) in: {path}")
    known = secret_hashes(rep)
    sizes = {s for s, _ in known}
    for path, full in walk(rootfs):
        if os.path.islink(full) or not os.path.isfile(full):
            continue
        size = os.path.getsize(full)
        if size in sizes:
            digest = hashlib.sha256(Path(full).read_bytes()).hexdigest()
            if (size, digest) in known:
                rep.fail(f"{path} is identical to local secret {known[(size, digest)]}")

    if rep.failures == before:
        rep.ok("no private keys, credentials, build paths or local secrets")


# ----------------------------------------------------------- accounts, misc

def check_accounts(rootfs: Path, rep: Report) -> None:
    rep.section("accounts")
    before = rep.failures
    for line in (rootfs / "etc/shadow").read_text().splitlines():
        user, pw = line.split(":")[:2]
        if pw == "" or pw.startswith("$"):
            rep.fail(f"account {user} has a {'empty' if pw == '' else 'set'} password in the image")
    for line in (rootfs / "etc/passwd").read_text().splitlines():
        f = line.split(":")
        if 1000 <= int(f[2]) < 60000:
            rep.fail(f"regular user {f[0]} exists in the image")
    for home in (rootfs / "home", rootfs / "root"):
        # an empty ~/.ssh directory (mode 0700) is created by openssh; files in it are not allowed
        # empty directories (~/.ssh from openssh, ~/.cache) hold nothing; files are not allowed
        extra = [p.name for p in home.iterdir() if p.name not in (".bashrc", ".profile")
                 and not (p.is_dir() and not p.is_symlink() and not any(p.iterdir()))] if home.is_dir() else []
        if extra:
            rep.fail(f"/{home.name} is not empty: {', '.join(sorted(extra))}")
    if rep.failures == before:
        rep.ok("no passwords, no users, empty /home and /root")


def check_leftovers(rootfs: Path, rep: Report) -> None:
    rep.section("leftovers")
    before = rep.failures
    sources = list((rootfs / "etc/apt").glob("sources.list")) + list((rootfs / "etc/apt/sources.list.d").glob("*"))
    for src in sources:
        for line in src.read_text().splitlines():
            for uri in re.findall(r"(?:https?|file|cdrom|copy):[^\s\]]+", line):
                # file:/run/live/medium is the live medium itself; installers replace it
                if uri == "file:/run/live/medium":
                    continue
                if not re.match(r"https?://(deb\.debian\.org|security\.debian\.org|genotomi\.github\.io)/", uri):
                    rep.fail(f"unexpected APT source in /{src.relative_to(rootfs)}: {uri}")
    debs = list((rootfs / "var/cache/apt/archives").glob("*.deb"))
    if debs:
        rep.fail(f"{len(debs)} cached .deb files in /var/cache/apt/archives")
    machine_id = rootfs / "etc/machine-id"
    if machine_id.exists() and machine_id.read_text().strip() not in ("", "uninitialized"):
        rep.fail("/etc/machine-id is set: every installation would share it")
    if rep.failures == before:
        rep.ok("no build repositories, cached packages or fixed machine id")


def check_iso_tree(iso_files: list[str], rep: Report) -> None:
    rep.section("iso")
    bad = [f for f in iso_files if not ISO_ALLOWED.search(f)]
    for f in bad:
        rep.fail(f"unexpected file on the ISO outside the root file system: {f}")
    if not bad:
        rep.ok(f"{len(iso_files)} files on the ISO, all boot, live or installer files")


# ----------------------------------------------------------------------- main

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("iso", type=Path)
    parser.add_argument("--edition", choices=("desktop", "server"))
    parser.add_argument("--keep", action="store_true", help="keep the extracted file system")
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("run as root: the file system must be extracted with its permissions", file=sys.stderr)
        return 2
    iso = args.iso.resolve()
    edition = args.edition or ("server" if "-server-" in iso.name else "desktop")
    work = WORK / "audit" / iso.stem
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)

    rep = Report()
    rep.lines.append(f"Erik OS ISO audit: {iso.name} ({edition})")
    print(f"extracting {iso.name} ...", flush=True)
    rootfs, iso_files = extract(iso, work)
    owned, owner = owned_paths(rootfs)
    allow, modified_ok = load_allowlist(edition)

    check_packages(rootfs, rep, WORK / "audit" / "indexes", iso.with_name(iso.name + ".manifest"))
    verified = check_integrity(rootfs, rep, modified_ok)
    check_files(rootfs, rep, allow, owned)
    check_secrets(rootfs, rep, owner, verified)
    check_accounts(rootfs, rep)
    check_leftovers(rootfs, rep)
    check_iso_tree(iso_files, rep)

    verdict = "FAIL" if rep.failed else "PASS"
    rep.lines.append(f"\nResult: {verdict}")
    out = iso.with_name(iso.name + ".audit.txt")
    out.write_text("\n".join(rep.lines) + "\n")
    print(f"{verdict}: report {out}")
    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)
    return 1 if rep.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
