# Changelog

All notable changes to Erik OS are recorded here, following the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. Versions
below 1.0 are unnamed development snapshots (technical prototypes).

## [0.4] - 2026-10-01

Built with `scripts/build-iso.sh all` (development build, zstd). Both ISOs
passed `scripts/audit-iso.py` (desktop 1739 packages, server 290 packages).

### Added

- Erik ASCII logo, generated from the Erik logo, shipped by `erik-base` as
  `/usr/share/erik/artwork/erik-logo.txt`. It is used wherever text shows
  the logo.
- `fastfetch` (Debian `main`) with a system-wide Erik configuration: green
  Erik logo with system information beside it. It replaces neofetch, which
  Debian 13 does not ship.
- `lm-sensors` (`sensors`) and `procps` (`watch`, `top`, `free`) in both
  editions.
- ASCII logo in the server login banner (`erik-server-base` 0.2.0).
- `scripts/new-pc.ps1`: installs the newest ISO into a fresh virtual PC from
  a virtual USB stick.

### Changed

- `erik-base` 0.4.0, `erik-server-base` 0.2.0.

### Known issues

- 0.4 has not yet been booted in a virtual machine; it was checked in a
  clean Debian 13 chroot (fastfetch shows "OS: Erik OS 0.4", the server
  banner shows the logo, `sensors` and `watch` run).
- Same as 0.3: Debian boot menu and boot splash, the live session starts in
  the GNOME overview, the server console still says Debian.

## [0.3] - 2026-10-01

First release built from Erik Debian packages, and the first with separate
desktop and server editions. Audit PASS: desktop 1736 packages, server 285
packages.

### Added

- Erik packages: `erik-archive-keyring`, `erik-base`, `erik-theme` 0.2.0,
  `erik-desktop-base` 0.2.0 (desktop), `erik-server-base` (server).
  Every Erik change is now a Debian package; installed systems receive
  changes through APT.
- Server edition: headless, OpenSSH, text installer, automatic console
  login in the live session, Erik OS login banner in four languages.
- `erik-theme` command (`list`, `set`, `reset`, `--json`) and the Erik
  Appearance app (`erik-theme-gui`, GTK 4 and libadwaita, four languages):
  wallpaper, light or dark style, accent colour, restore defaults. It opens
  once at the first login of an installed system.
- Erik logo on the GDM login screen (`vendor-logos` alternative, priority
  100; removing the package restores Debian's).
- License policy (`docs/LICENSING.md`) enforced by
  `scripts/check-licenses.py`.
- ISO audit `scripts/audit-iso.py` (package origin against Debian's signed
  indexes, file integrity, files nobody owns, private keys, local secrets,
  build machine names and paths, accounts, APT sources) with an audit report
  and a package manifest per ISO. Its test, `scripts/tests/test-audit-iso.sh`,
  plants ten kinds of problems into a copy of an ISO and fails unless all
  are caught.
- Signed APT archive configuration (`reprepro`, channels `testing` and
  `stable`) and the archive signing key (ed25519, expires 2029-09-30).
- Faster builds: build tree in RAM, package cache on disk, zstd for
  development builds and xz for `--release`, desktop and server in parallel
  (`all`). Desktop build time dropped from about 12 minutes to 3 minutes 21
  seconds.
- Build host moved from a VirtualBox VM to a WSL2 Debian 13 distribution;
  VirtualBox remains for boot and installation tests.

### Changed

- Only Debian `main`: `non-free-firmware` removed. Some Wi-Fi cards and GPUs
  may not work out of the box.
- The system identifies as Erik OS (`/usr/lib/os-release`: `ID=erik`,
  `ID_LIKE=debian`).
- Wallpapers and logo are GPL-3.0-only and live only in `erik-theme`; only
  Erik wallpapers are offered, the Debian and GNOME lists are hidden with
  `dpkg-divert`. Default wallpaper `dark`, green accent.
- The installer greets with "Welcome to the Erik OS 0.3 installer"; Debian's
  launcher file is moved aside with a diversion instead of being overwritten.
- Live-build tree split into `editions/common`, `editions/desktop` and
  `editions/server`.

### Fixed

- The installer now opens by itself in the live session. In 0.2 the
  autostart script checked for a build machine user name instead of the
  live user, so it never started.
- Wallpaper handling no longer overwrites files of other packages, which
  `apt upgrade` would have undone.
- No GNOME tour, before or after installation: `erik-desktop-base` conflicts
  with `gnome-tour`.

### Known issues

- The boot menu reads "Debian GNU/Linux 13" and has no timeout; the boot
  splash (Plymouth) still shows the Debian logo.
- The live session starts in the GNOME overview, so the installer window
  has no keyboard focus until the overview is closed.
- Server console: `/etc/issue`, `/etc/motd` and the host name still say
  Debian.
- The Erik APT source is installed but disabled until the archive is
  published.
- Not tested: server installation to disk; German, Spanish and Turkish
  installations.

## [0.2] - 2026-10-01

### Added

- Eight Erik wallpapers; default wallpaper `dark.jpg`; only Erik wallpapers
  shown in GNOME Settings.
- Calamares installer meant to start automatically in the live session.
- Wallpaper support in `scripts/stage-artwork.py`.

### Changed

- GNOME Tour and GNOME Initial Setup disabled.
- Calamares branding version updated to 0.2.

### Known issues

- 0.2 was never tested and was replaced by 0.3. Code review found that the
  installer autostart would not have worked (see 0.3, Fixed) and that the
  wallpaper script overwrote files of other packages.

## [0.1] - 2026-09-30

First technical prototype, desktop edition only.

### Added

- Debian 13 trixie, GNOME 48, live-build and the Calamares installer (full
  disk installation).
- Erik branding in the installer (logo, branding descriptor, slideshow).
- Interface languages English, German, Spanish and Turkish.
- Tested in VirtualBox (UEFI, 1 virtual CPU, 40 GB disk): installation
  completed, the installed system booted to GDM and a GNOME session.

### Known issues

- The GNOME tour is shown at first login (fixed in 0.2).
- The installer does not start automatically (attempted in 0.2, fixed in
  0.3).
- Wallpapers and boot screens are Debian's (fixed in 0.2 and 0.3, boot
  surfaces still open).
- The test host needed 1 virtual CPU with paravirtualization disabled to
  avoid a VirtualBox RCU timing stall; this is a host quirk, not a hardware
  requirement.
