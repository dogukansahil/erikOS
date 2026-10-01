# How Erik OS is built

Erik OS is neither a remastered ISO nor a Linux From Scratch system. It is
built the way Debian builds its own live images, and the way Kali Linux,
Tails and PureOS build theirs: with **live-build**, from source-controlled
configuration, on a clean Debian system, every time from zero.

## Build system

Use Debian 13 (trixie) as root: a WSL2 Debian 13 distribution, a virtual
machine or a physical machine. Required tools:

```sh
apt-get install --no-install-recommends live-build debootstrap squashfs-tools \
  xorriso dpkg-dev debhelper devscripts lintian reprepro gnupg fakeroot \
  python3 rsync ca-certificates apt-file build-essential
```

Run the scripts from the repository root. Builds work on the Linux file
system (by default under `~/erik-work`); the scripts copy the sources there.
Under WSL2, do not build on the Windows drive mounted under `/mnt`: it is
slow and makes every file look executable. Further notes on the local layout
are in [`../build-environment/README.md`](../build-environment/README.md).

```sh
sh scripts/build-packages.sh              # all packages (or name one: erik-theme)
sh scripts/build-iso.sh desktop           # or: server, or: all
sh scripts/build-iso.sh --release all     # release build (xz compression)
```

## The pipeline

```
packages/*             ->  build-packages.sh  ->  erik-*.deb (lintian, license check)
                                                     |
editions/common + <ed> ->  build-iso.sh  ->  live-build:
                                               1. debootstrap: a fresh Debian 13 base,
                                                  downloaded and signature-checked
                                                  from deb.debian.org (main only)
                                               2. install the edition's package lists
                                                  plus the Erik packages
                                               3. run the edition hooks
                                               4. pack the root file system (squashfs)
                                               5. add the boot loader, write the ISO
                                                     |
                                           audit-iso.py  ->  PASS / FAIL report
```

Nothing is copied from a running machine, and no existing ISO is modified.
Delete every ISO and the same Git revision produces the same system again
(with the caveat that the Debian archive moves on; see
[`ARCHITECTURE.md`](ARCHITECTURE.md), base archive strategy).

### Why not remaster an ISO?

Remastering (unpack a Debian ISO, change files, repack) carries over
whatever was in that ISO, cannot be reproduced from source, and edits files
that the next `apt upgrade` overwrites. It is how unmaintainable
distributions are made.

### Why not Linux From Scratch?

LFS compiles every program by hand and has no package manager or security
updates. Erik OS users get Debian's security updates for every program
through APT, and Erik's own changes through the Erik archive. LFS is a
learning exercise, not a way to ship a supported system.

## Rules that keep it professional

- **Every Erik change is a Debian package.** Installed systems receive
  fixes through `apt upgrade`; no one needs a new ISO for a theme change.
- **Other packages' files are never edited.** Defaults use GSettings
  overrides; replacements use `dpkg-divert` or `update-alternatives`.
  The audit verifies every Debian file byte for byte.
- **Only Debian `main` plus Erik.** See [`LICENSING.md`](LICENSING.md).
- **Every ISO is audited** (`scripts/audit-iso.py`): package origins against
  Debian's signed indexes, file integrity, files nobody owns, private keys,
  local secrets, build machine names and paths, passwords, users, leftover
  build repositories, extra files on the ISO. The auditor itself is tested:
  `scripts/tests/test-audit-iso.sh` plants ten kinds of problems into a copy
  of an ISO and fails unless all ten are caught.

## Build speed

Measured on an Intel i5-14600KF (20 threads) with 64 GB RAM, WSL2 given
48 GB:

- The build tree lives in RAM (tmpfs) when there is room. dpkg flushes every
  file to disk (`fsync`) while installing ~1700 packages; in RAM that costs
  nothing.
- The package cache stays on disk (`~/erik-work/cache/<edition>`), so
  rebuilds do not download again.
- Development builds compress with zstd (fast); `--release` uses xz
  (smallest download).
- `build-iso.sh all` builds desktop and server at the same time.
- Each build log (`~/erik-work/logs/<edition>.log`) carries the elapsed time
  on every line, so slow stages are visible.

A GPU cannot speed this up: the work is installing packages and compressing
with the CPU.

## What is still missing for a 1.0 release

- Pinning the Debian archive to a dated snapshot (snapshot.debian.org), so a
  rebuild months later produces the same package versions.
- A source ISO (`lb config --source true`) next to each release: the GPL
  requires us to offer the source of every GPL program we distribute.
- Signing `SHA256SUMS` with the Erik release key.
- Building releases on a clean CI runner instead of a developer machine.

See [`../ROADMAP.md`](../ROADMAP.md).
