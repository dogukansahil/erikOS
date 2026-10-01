# Erik OS

Erik OS is a Debian 13 (trixie) and GNOME based distribution for the life
sciences, by [Genotomi](https://github.com/Genotomi). It is built with
[live-build](https://live-team.pages.debian.net/live-manual/) and comes in
two editions:

- **Desktop:** GNOME with the Calamares installer.
- **Server:** headless, with OpenSSH and the text installer.

Erik OS is available in English, German, Spanish and Turkish (EN/DE/ES/TR).
This is a requirement, not an option: the installer, the system, Erik tools
and user-facing documentation all have to support the four languages.

## Status

Erik OS is in early development. The current version (see `VERSION`) is
**0.4**: a series of development snapshots, unnamed technical prototypes
that are meant for testing in virtual machines. They are not ready for
production use and receive no security support (see
[`SECURITY.md`](SECURITY.md)).

Version 1.0 is planned with the codename **Bruno**, and 2.0 with the
codename **Rumi**. What is done and what comes next is in
[`ROADMAP.md`](ROADMAP.md); what changed in each version is in
[`CHANGELOG.md`](CHANGELOG.md).

## License rule (binding)

Everything Erik OS writes, including tools, scripts, configuration and
artwork, is licensed **GPL-3.0-only**. Third-party software comes only from
Debian **`main`**: no `contrib`, `non-free` or `non-free-firmware`, no
proprietary drivers, no foreign repositories and no foreign branding in the
images. Details and enforcement: [`docs/LICENSING.md`](docs/LICENSING.md).
The build stops when `scripts/check-licenses.py` finds a violation.

## Hardware baseline

- **Architecture:** Intel and AMD x86_64 (amd64).
- **RAM:** 8 GB for the desktop edition, 4 GB for the server edition.
- **Storage:** 256 GB for both editions.
- **GPU compute:** only what Debian `main` provides. Proprietary GPU
  drivers and runtimes such as NVIDIA CUDA are not part of any image.
- **Firmware:** only free firmware from `main`. Some Wi-Fi cards and GPUs
  may not work out of the box.

## Repository layout

| Path | Content |
|---|---|
| `packages/` | Debian source packages of everything Erik installs: `erik-archive-keyring`, `erik-base`, `erik-theme`, `erik-desktop-base`, `erik-server-base`. See [`packages/README.md`](packages/README.md). |
| `archive/conf/` | `reprepro` configuration of the Erik APT archive (channels `testing` and `stable`). |
| `editions/common/`, `editions/desktop/`, `editions/server/` | live-build configuration: the shared part and the two editions. |
| `scripts/` | Build, audit, signing, publishing and check scripts. |
| `docs/` | Architecture, building, licensing, installation notes and decision records. |
| `VERSION`, `LICENSE` | Current version; GPL-3.0 text. |
| `build-environment/` | Local only, never committed: build VM disks, caches, the private archive signing key and the generated APT tree (`archive-out/apt/`). Only its README is tracked. |

Release files (ISOs, checksums, audit reports) are never committed to Git.

## Build

You need a Debian 13 system with live-build, for example a WSL2 Debian 13
distribution or a virtual machine. The setup is described in
[`docs/BUILDING.md`](docs/BUILDING.md) and
[`build-environment/README.md`](build-environment/README.md).
Run as root inside the project directory:

```sh
sh scripts/build-packages.sh              # build the Erik packages (license check, lintian)
sh scripts/build-iso.sh desktop           # or: server, or: all
sh scripts/build-iso.sh --release all     # release build (xz compression)
```

`build-iso.sh` runs `scripts/audit-iso.py` on every finished ISO; an ISO
whose audit fails is not released. Test the result by booting it in a
virtual machine.

## Releases

ISO images, `SHA256SUMS` and audit reports are published on GitHub Releases
of this repository, never inside the Git history. Installed systems get
Erik updates through APT; a new ISO is only needed for new installations.

## Related repositories

- `Genotomi/erikos-tools` (planned): Erik command line tools. They are
  currently demonstrations and will be renamed before they are packaged.
- `Genotomi/erik.genotomi`: the Erik OS website.

## Documentation

- [`CONTRIBUTING.md`](CONTRIBUTING.md): how to contribute
- [`SECURITY.md`](SECURITY.md): reporting vulnerabilities
- [`ROADMAP.md`](ROADMAP.md): plans
- [`CHANGELOG.md`](CHANGELOG.md): version history
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): how the system is put together
- [`docs/BUILDING.md`](docs/BUILDING.md): how it is built
- [`docs/LICENSING.md`](docs/LICENSING.md): license policy
- [`docs/installation/README.md`](docs/installation/README.md): installer notes and test pass
- [`docs/decisions/`](docs/decisions/): decision records
