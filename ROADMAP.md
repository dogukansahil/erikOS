# Erik OS roadmap

This file is the single public source of plans for Erik OS. Principles and
architecture are in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md); finished
work is in [`CHANGELOG.md`](CHANGELOG.md).

`[x]` done, `[ ]` planned, `[-]` postponed or dropped. Plans can change.

Versions below 1.0 are unnamed development snapshots. 1.0 is codenamed
**Bruno**, 2.0 **Rumi**.

## Current: 0.4

- [x] Debian 13 and GNOME 48 with the Calamares installer, desktop and
  server editions built with live-build
- [x] Everything Erik adds is a Debian package; installed systems update
  through APT
- [x] License rule enforced by the build (GPL-3.0-only, Debian `main` only)
- [x] ISO audit on every build, with a tested auditor
- [x] Erik appearance (wallpapers, logo, GDM logo, Erik Appearance app)
- [x] ASCII logo, fastfetch, `sensors`, `watch`
- [x] Desktop: full installation and first boot verified in a virtual machine
  (0.3)
- [ ] Boot 0.4 in a virtual machine and check fastfetch in a real terminal
- [ ] Server: full installation to disk
- [ ] Desktop installation in German, Spanish and Turkish

## Next: 0.5 candidates

- [ ] Live session should not start in the GNOME overview, so the installer
  gets keyboard focus
- [ ] Publish the Erik APT archive and enable the `erik.sources` entry
  (`Enabled: yes`)
- [ ] Favourite apps (GNOME dash) and default browser bookmarks
- [ ] Python and R work environments
- [ ] First science tool packaged from `erikos-tools`
- [ ] Smaller ISO

## Before 1.0

### Remove remaining Debian branding

- [ ] GRUB boot menu: "Debian GNU/Linux 13" title (live-build default), no
  menu timeout
- [ ] Plymouth boot splash (Debian theme from `desktop-base`) replaced by an
  Erik theme in `erik-theme`
- [ ] Server console: `/etc/issue`, `/etc/motd` and the host name `debian`
  (through `erik-base` diversions and `hostname=erikos`)
- [ ] Text installer of the server edition (debian-installer titles)
- [ ] `calamares-settings-debian` replaced by an Erik settings package
- [ ] dpkg vendor: `/etc/dpkg/origins/default` still says `debian`

### Release engineering

- [ ] GPL source ISO with each release (`lb config --source true`)
- [ ] Reproducible builds: pin each release to a dated
  snapshot.debian.org state of the Debian archive, so a rebuild months
  later gives the same package versions
- [ ] Later: an own Erik archive mirror built with aptly (decided:
  snapshot first, own archive later; see
  [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md))
- [ ] Signed `SHA256SUMS` (Erik release key)
- [ ] CI release builds on a clean runner
- [ ] Publish the Erik APT archive (channels `testing` and `stable`)

### Testing

- [ ] Full installation tests: server edition, and desktop in DE, ES and TR
- [ ] Offline installation
- [ ] Encrypted installation (first boot and passphrase entry)
- [ ] Real hardware tests
- [ ] Secure Boot tests (no support is claimed before they pass)
- [ ] Accessibility test
- [ ] Security scan

### Documentation and project

- [ ] Full documentation: installation, usage, development
- [ ] Release notes and support policy
- [ ] Website and download portal (separate repository)
- [ ] At least 3 finished Erik command line tools (from `erikos-tools`)
- [ ] One biological analysis workflow verified end to end

## Future features

### Erik Settings (`erik-settings`)

All settings designed by Erik in one place: a GTK 4 and libadwaita app in
four languages, every section updated by its own Debian package.

- [ ] Appearance: the current Erik Appearance app (`erik-theme-gui`) moves
  here
- [ ] SSH: install, enable, disable or remove the OpenSSH server, choose
  password or key-only login, manage authorized keys, show status and
  address (privileges through polkit)
- [ ] Drivers and CUDA: opt-in install, update and removal of the NVIDIA
  driver and CUDA from the vendor's official source, after the user accepts
  the license in the tool. Never in the ISO or in the Erik archive; removal
  leaves no trace. See rule 2a in [`docs/LICENSING.md`](docs/LICENSING.md); a
  decision record is written first.
- [ ] Updates: Erik and Debian updates, channel choice (stable or testing)
- [ ] Command line equivalent: every setting also available as an
  `erik-settings` command with JSON output (for scripts and agents)

### Erik boot animation

- [ ] Erik Plymouth theme (logo and animation) in `erik-theme`, registered as
  an alternative of `default.plymouth`; Debian's theme stays as fallback
- [ ] Matching GRUB menu and live ISO boot menu in the same design

### Science tools

- [ ] First tool from `erikos-tools`, renamed, packaged under `packages/`
  and published to the Erik archive
- [ ] Python and R environments, example data set and a first verified
  workflow

## 1.0 Bruno

First stable release, quality bar: ready for a DistroWatch application.

- [ ] Everything under "Before 1.0" above
- [ ] Signed Erik archive in use on installed systems
- [ ] Documented support policy with supported versions and end dates

## 2.0 Rumi

Long-term vision, not committed.

- [ ] Evaluate ARM64
- [ ] Cloud and container images
- [ ] Modular scientific profiles
- [ ] LLM based research assistant integration
