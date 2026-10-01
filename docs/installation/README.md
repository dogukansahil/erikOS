# Erik OS installer prototype

This document describes the desktop installer. The source tree targets Debian 13 (Trixie), amd64, GNOME, `live-build`, and Calamares. Erik's installer screen uses a light background, green accent, and the logo in `packages/erik-theme/artwork/logo.png`.

## What is wired up

> Since 0.3 the live-build tree is split into `editions/common/`, `editions/desktop/` and `editions/server/`, and Erik customisations are Debian packages under `packages/`. Paths below refer to `editions/desktop/`. Build with `sh scripts/build-iso.sh desktop` on a Debian 13 build system (see [`../BUILDING.md`](../BUILDING.md)).

- `auto/config` defines an ISO hybrid live image from Debian `main` only. `non-free-firmware` was removed on 2026-10-01 (`docs/LICENSING.md`).
- `config/package-lists/` installs GNOME, Calamares, Debian's tested Calamares settings, `erik-desktop-base`, and language packages for English, German, Spanish, and Turkish.
- `editions/common/config/includes.chroot/etc/locale.gen` lists the four initial UTF-8 locales. The common chroot hook generates them during the build.
- `config/includes.chroot/etc/calamares/branding/erik/` holds Erik's Calamares branding. `scripts/stage-artwork.py` copies its logo from `packages/erik-theme/artwork/logo.png`.
- `config/hooks/live/010-erik-installer.hook.chroot` switches only Calamares's branding name. Debian's disk, encryption, bootloader, and package operation sequence remains in the Debian settings package.
- `config/hooks/live/020-erik-live-installer.hook.chroot` opens the installer when the live session starts; it checks `boot=live`, so it does nothing on an installed system.
- The live desktop's install launcher has names and descriptions in all four languages. It retains Debian's `calamares-install-debian` wrapper because the wrapper handles live-session setup before starting Calamares.

## Build on a clean Debian Trixie machine

The normal way is `sh scripts/build-iso.sh desktop` (see [`../BUILDING.md`](../BUILDING.md)), which merges `editions/common` and the edition and runs live-build. The first full build was done in a Debian 13 virtual machine. To run the pieces by hand on a clean Debian 13 machine:

```sh
sudo apt update
sudo apt install live-build
python3 scripts/stage-artwork.py --check
```

then run `lb config` and `sudo lb build` in the merged edition tree that `build-iso.sh` prepares. The `auto/build` script checks the staged logo before building. Keep ISO files and build caches out of source control.

## Validated image

The first amd64 image was built and tested on 2026-09-30 and 2026-10-01. It is the Erik OS 0.1 technical prototype (kept locally, not in Git).

- File: `erikos-0.1-desktop-amd64.iso`
- Size: 2,164,260,864 bytes
- SHA256: `D8D932EE03172D618A72B347086359BED1CA36522D5FC41368BF70A9EC806443`
- Test VM: Oracle VirtualBox, UEFI, 40 GB empty virtual disk
- Result: Calamares completed installation, the ISO was detached, the installed disk booted, GDM accepted the created user, and GNOME started

On the current Windows host, VirtualBox showed Linux RCU timing stalls when the test VM used multiple virtual CPUs. The installed system completed first boot with 1 virtual CPU and paravirtualization disabled. Treat this as a host and VirtualBox compatibility note while testing, rather than a distribution hardware requirement.

## First VM acceptance pass

Use a disposable VM with UEFI, Secure Boot disabled, at least 4 GiB RAM, and an empty virtual disk of at least 25 GiB. The first English full disk installation pass is complete. Test the complete flow in German, Spanish, and Turkish. For each language, verify the install launcher, welcome screen, partition summary, first boot, desktop locale, and terminal locale. Repeat with the network disconnected. Test encrypted installation in a separate empty VM and verify both first boot and passphrase entry. Do not claim dual boot or Secure Boot support from this pass.

Calamares is the installer that performs disk operations on the ISO. The website lives in its own repository, `Genotomi/erik.genotomi`.

## Upstream reference

- [Debian live images](https://www.debian.org/CD/live/index)
- [Debian Calamares settings, Trixie](https://sources.debian.org/src/calamares-settings-debian/13.0.13-1/calamares/settings.conf)
- [Debian Calamares branding, Trixie](https://sources.debian.org/src/calamares-settings-debian/13.0.13-1/calamares/branding/debian/branding.desc)
- [Debian install launcher and wrapper](https://sources.debian.org/src/calamares-settings-debian/13.0.13-1/calamares-install-debian.desktop)
- [Trixie `lb config` options](https://manpages.debian.org/trixie/live-build/lb_config.1.en.html)
