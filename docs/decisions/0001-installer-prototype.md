# ADR 0001: Installer prototype

Status: provisional, pending ISO and VM tests  
Date: 2026-09-29

## Context

Erik OS needs a graphical installer for a Debian/GNOME live image. The first supported interface languages are English, German, Spanish, and Turkish. Installation must work without a network connection. Disk operations, encryption, UEFI boot, and the selected language passing into the installed system need verification.

## Decision for the first prototype

Use Calamares with Debian Trixie's `calamares-settings-debian` package. Debian's official live images already use Calamares, and its settings package supplies the partition, mount, filesystem copy, bootloader, and package operation sequence. Keep that sequence intact while applying Erik branding through a build hook and the Calamares branding directory. Keep Debian's launcher wrapper for live-session setup, but translate and brand the visible desktop entry.

Use `live-build` for the ISO. The `--debian-installer none` option disables a separate Debian Installer image path; Calamares remains in the live GNOME environment. Debian Installer remains a fallback if Calamares fails the VM acceptance pass.

The first prototype (0.1 and 0.2) included `non-free-firmware` for initial hardware coverage. This was superseded on 2026-10-01: images use Debian `main` only (see `docs/LICENSING.md`).

## Evidence and review gate

- [Official Debian live images](https://www.debian.org/CD/live/index)
- [Trixie Calamares settings](https://sources.debian.org/src/calamares-settings-debian/13.0.13-1/calamares/settings.conf)
- [Trixie branding descriptor](https://sources.debian.org/src/calamares-settings-debian/13.0.13-1/calamares/branding/debian/branding.desc)
- [Trixie live-build options](https://manpages.debian.org/trixie/live-build/lb_config.1.en.html)

Accept this choice only after a clean ISO build and VM installs verify the four languages, offline operation, UEFI boot, and encrypted disk recovery. A visual prototype alone is not installation evidence.
