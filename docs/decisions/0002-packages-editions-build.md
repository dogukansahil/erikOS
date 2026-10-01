# 0002: Erik packages, desktop/server editions and the WSL build

Date: 2026-10-01. Status: accepted.

## Context

Up to 0.2, Erik customisations were shell hooks inside the live-build tree.
They edited files owned by other Debian packages (wallpaper lists), so an
`apt upgrade` on an installed system would undo them, and an installed
system could not receive Erik changes at all. Wallpapers were copied into
the image but had no owner. The 0.2 installer autostart hook contained a
Windows user name instead of a live-session check, so it never started the
installer. Builds ran in a VirtualBox VM over SSH with a stored password.

## Decision

1. **Everything Erik installs is a Debian package.** Sources live in
   `packages/<name>/` as standard `debian/` source packages
   (`3.0 (native)`, debhelper 13), built with `dpkg-buildpackage` and checked
   with `lintian`. Installed systems receive changes through
   `sudo apt update && sudo apt upgrade`; new tools through
   `sudo apt install erik-<tool>`.
2. **Package roles.**
   - `erik-archive-keyring`: repository signing key and APT source entry.
   - `erik-base`: system identity (os-release); shared by every edition.
   - `erik-theme`: the single home of Erik artwork and appearance settings,
     plus the `erik-theme` command. Future appearance settings go here.
   - `erik-desktop-base`: desktop edition defaults (GNOME).
   - `erik-server-base`: server edition defaults (headless, OpenSSH).
3. **Files of other packages are never edited.** Defaults use GSettings
   override files; files that must change (os-release, wallpaper lists) use
   `dpkg-divert` and are restored when the Erik package is removed.
4. **Editions.** `editions/common/` holds what both images share;
   `editions/desktop/` (GNOME, Calamares) and `editions/server/` (no GUI,
   text installer) hold the rest. `scripts/build-iso.sh <edition>` merges
   them on the Linux file system and runs live-build.
5. **Repository.** A signed APT repository built with `reprepro`
   (`archive/conf/`), channels `testing` and `stable`, served statically
   (published separately from this repository; location to be decided). The private signing key stays in
   `build-environment/secrets/` and is never committed.
6. **Build host.** Packages and ISOs are built in the WSL2 Debian 13 distro
   `ErikOS-Build`, whose disk lives in `build-environment/wsl/disk/`.
   VirtualBox remains only for booting and installing ISOs, which WSL cannot
   do.
7. **License policy.** `docs/LICENSING.md`: Erik work is GPL-3.0-only,
   third-party software only from Debian `main`, enforced by
   `scripts/check-licenses.py`.

## Consequences

- The installer autostart is now an ISO-only hook that checks `boot=live`.
- Artwork moved from `assets/` into `packages/erik-theme/`.
- Later (2026-10-01), before the first Git commit, the layout was flattened:
  `github/packages` became `packages/`, `github/repo/conf` became
  `archive/conf/`, `github/scripts` merged into `scripts/`, and the generated
  APT tree moved out of the repository to `build-environment/archive-out/apt/`.
- Hardware that needs non-free firmware will not work out of the box.
- `/etc/skel` is not used (Debian policy); the GNOME welcome tour is turned
  off with a GSettings key instead. `gnome-initial-setup` is not part of the
  desktop image.
- The Erik APT source ships disabled (`Enabled: no`) until the repository is
  actually published, so installed systems never fail `apt update`.
