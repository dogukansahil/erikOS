# Erik OS packages

Everything Erik OS installs on a system is a Debian package built from this
directory. Users get Erik tools the normal Debian way:

```sh
sudo apt update
sudo apt install erik-<tool>      # for example: sudo apt install erik-theme
```

All packages here are GPL-3.0-only and may depend only on Debian `main`.
Read [`../docs/LICENSING.md`](../docs/LICENSING.md) before adding anything.

## Layout

| Path | What it is |
|---|---|
| `packages/<name>/` | One source package per directory, standard `debian/` layout (this directory) |
| `archive/conf/` | `reprepro` configuration of the Erik APT archive: channels `testing` and `stable` |
| `scripts/` | Build, sign and publish scripts (`build-packages.sh`, `publish-repo.sh`, `create-signing-key.sh`) |
| `build-environment/archive-out/apt/` | Generated, signed APT tree. Local, published separately, never committed |

## Packages

| Package | Edition | Purpose |
|---|---|---|
| `erik-archive-keyring` | all | Repository signing key and APT source entry |
| `erik-base` | all | System identity: `/usr/lib/os-release` says Erik OS, `ID_LIKE=debian`; ASCII logo and fastfetch configuration |
| `erik-theme` | desktop | Wallpapers, logo, login screen logo, GNOME appearance defaults, `erik-theme` command and the Erik Appearance app |
| `erik-desktop-base` | desktop | GNOME desktop defaults; pulls in `erik-base` and `erik-theme`; conflicts with `gnome-tour` |
| `erik-server-base` | server | Headless defaults, login banner, OpenSSH |

`erik-theme` is the only place for Erik artwork. To change a wallpaper or
the logo, edit `packages/erik-theme/backgrounds/` or `artwork/`, raise the
version in `debian/changelog` and rebuild. New appearance settings (icons,
GTK, GRUB and Plymouth themes, fonts) belong in this package too.

**Erik Appearance** (`erik-theme-gui`, GTK 4 and libadwaita) chooses the
wallpaper, light or dark style and accent colour. It opens once after the
first login of an installed system (never in the live session), replacing
the GNOME tour, and stays in the app grid. It is updated by `apt upgrade`
together with the package. The vendor logo (GDM login screen) is Erik's
through the `vendor-logos` alternative; removing `erik-theme` restores
Debian's.

```sh
erik-theme list            # installed wallpapers, current one marked
erik-theme set lake        # desktop and lock screen
erik-theme reset           # back to the Erik defaults
erik-theme list --json     # stable machine-readable output
```

## Build

Run as root on a Debian 13 build system (see
[`../docs/BUILDING.md`](../docs/BUILDING.md)), from the repository root:

```sh
sh scripts/build-packages.sh               # all packages
sh scripts/build-packages.sh erik-theme    # one package
```

The script runs the license check, copies each package to the Linux file
system, fixes file modes, refuses CRLF line endings, builds with
`dpkg-buildpackage` and fails on any `lintian` error. Output:
`~/erik-work/debs/`.

## Add a new tool, for example `erik-api`

1. Write the tool in its own repository (the Erik command line tools are
   planned for `Genotomi/erikos-tools`) with its own tests, README and
   `LICENSE`. Help, warnings and errors in English, German, Spanish and
   Turkish; command names, JSON fields and exit codes the same in every
   language (see [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)).
2. Create `packages/erik-api/debian/` by copying `erik-theme/debian/` and
   changing the name, description, `Depends` (Debian `main` only) and
   `install` file. Keep `debian/copyright` at `GPL-3.0-only`.
3. Put `SPDX-License-Identifier: GPL-3.0-only` at the top of every source
   file.
4. `sh scripts/build-packages.sh erik-api` until it passes.
5. Publish to `testing`, test with `apt install erik-api` on a clean system,
   then promote to `stable`.

## Sign and publish

One time only, create the signing key. The private key stays in
`build-environment/secrets/` (local, never committed); the public key is
exported into `erik-archive-keyring`.

```sh
sh scripts/create-signing-key.sh
```

Then, after each package build:

```sh
sh scripts/publish-repo.sh testing     # new packages always go here first
sh scripts/publish-repo.sh stable      # after testing passed
```

The generated tree in `build-environment/archive-out/apt/` is a complete
static APT archive. It is not committed to this repository. It will be
published from there to a separate location (GitHub Pages of a dedicated
repository, or a server); the choice is still to be decided. The planned URL
`https://genotomi.github.io/erik-packages` is already in
`erik-archive-keyring` (`sources/erik.sources`), but the entry ships with
`Enabled: no`. When the archive is live, set it to `Enabled: yes`, raise the
keyring version and publish; installed systems pick it up with
`apt upgrade`. If the location differs, update the URL in the same change.

GitHub limits single files to 100 MB and Pages sites to about 1 GB. Large
data never goes into packages; tools download it at run time.

## Verified on 2026-10-01

In a clean Debian 13 chroot: all five packages install, reinstall and purge
without errors; os-release and the Debian/GNOME wallpaper lists come back
after purge with no leftover diversions; GNOME defaults read back as the
Erik wallpaper, green accent and disabled welcome tour; `apt install
erik-theme` works from the signed local archive, and a tampered
`InRelease` is rejected.
