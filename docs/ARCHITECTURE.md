# Erik OS architecture

This is a concise description of how Erik OS is put together. How to run a
build is in [`BUILDING.md`](BUILDING.md); the license rules are in
[`LICENSING.md`](LICENSING.md); plans are in [`../ROADMAP.md`](../ROADMAP.md).

## Principle: the distribution is a Git repository

The product is not an ISO file. It is this versioned repository, from which
an ISO is produced from zero on a clean Debian system. Nothing is copied from
a running machine and no existing ISO is modified. Every customisation is
reviewable source: a package, a configuration file or an idempotent hook that
stops the build on error. A change that exists only on a developer's machine
cannot enter a release.

## Base and editions

Erik OS is built with live-build from Debian 13 (trixie), archive area
`main` only, for amd64. There are two editions:

- **desktop:** GNOME 48, Calamares installer.
- **server:** headless, OpenSSH, text installer (debian-installer).

`editions/common/` holds what both share (languages, locales, the common
package lists); `editions/desktop/` and `editions/server/` hold the rest.
`scripts/build-iso.sh` merges `common` and one edition on the Linux file
system and runs live-build.

## Erik packages

Everything Erik installs is a Debian source package in `packages/`
(`3.0 (native)`, debhelper 13, checked by lintian).

```
erik-archive-keyring
        ^
        |
    erik-base  <---------------------- erik-server-base   (server edition)
        ^
        |
erik-desktop-base ------> erik-theme                      (desktop edition)
```

Arrows point to the dependency. In detail:

| Package | Depends on | Role |
|---|---|---|
| `erik-archive-keyring` | | Archive signing key and APT source entry |
| `erik-base` | `erik-archive-keyring` | System identity (`os-release`, `ID=erik`, `ID_LIKE=debian`), ASCII logo, fastfetch configuration |
| `erik-theme` | Python, GTK 4, libadwaita | The only home of Erik artwork and appearance settings, `erik-theme` command, Erik Appearance app |
| `erik-desktop-base` | `erik-base`, `erik-theme` | GNOME defaults; conflicts with `gnome-tour` |
| `erik-server-base` | `erik-base` | Headless defaults, login banner; recommends OpenSSH |

Rules that keep packages upgrade-safe: files of other packages are never
edited (GSettings overrides, `dpkg-divert`, `update-alternatives` only), and
diversions are undone when the Erik package is removed.

## Erik APT archive

The Erik archive is a static, signed APT tree produced by `reprepro`
(configuration in `archive/conf/`) with two channels:

- `testing`: every new package version goes here first.
- `stable`: a version is promoted from `testing` after it has been tested.

The tree is generated into `build-environment/archive-out/apt/` and is not
part of this repository; it will be published separately (location still to
be decided). The archive contains only Erik packages, never copies of Debian
packages. The signing key is described in [`../SECURITY.md`](../SECURITY.md).
The APT source entry ships in `erik-archive-keyring` and stays disabled
(`Enabled: no`) until the archive is published.

## Update model

Installed systems and installation media are separate cycles.

- **Installed systems** receive Erik packages and Debian updates through
  APT (`sudo apt update && sudo apt upgrade`). A theme fix or a new tool
  never needs a new ISO.
- **A new ISO** is built for new installations: a fresh installer, a newer
  Debian base, fewer updates to download after install. It is not an upgrade
  path. The ISO version states how recent the installation medium is; the
  APT package versions state the state of an installed system.

## The audit gate

After every build, `scripts/audit-iso.py` opens the finished ISO and checks
package origin against Debian's signed indexes, file integrity, files nobody
owns, private keys, local secrets, build machine names and paths, accounts,
APT sources and the ISO root. It writes a report and a package manifest. An
ISO that fails is not released. The auditor is itself tested by
`scripts/tests/test-audit-iso.sh`, which plants known problems and requires
all of them to be caught. Before the audit, `scripts/check-licenses.py`
enforces the license rules and `lintian` checks every package.

## Base archive strategy

Today, builds use the live Debian archive, so a rebuild on another day can
yield different package versions. The decided path to reproducible releases:

1. **Snapshot first.** Each release is pinned to a dated state of
   snapshot.debian.org, and the date is recorded with the release. The same
   Git revision then builds the same package set at any time.
2. **Own archive later.** An Erik mirror of the Debian packages in use,
   built with aptly.

Trade-off of the own archive: it gives full control and independence from
snapshot availability, but security updates for Debian packages then reach
users through the Erik archive, so Erik has to follow Debian security
announcements closely and republish quickly. That responsibility is accepted
only once the snapshot step is established.

## CLI contract for Erik tools

Erik tools are used by people, scripts and LLM based agents through the same
documented interface. A feature that exists only in a GUI is not complete.
(The GNOME desktop itself being graphical does not conflict with this; the
rule applies to the functions of Erik's own science and management tools.)

- Standalone `erik-<tool>` commands; every command has `--help` and
  `--version`; long option names, clear subcommands, documented defaults;
  shell completion.
- Human-readable output by default and JSON for automation
  (`--format json`): a single JSON result that follows a versioned schema.
  Long jobs may offer an explicitly selected JSON Lines event stream, never
  mixed into the normal JSON.
- `stdout` carries only the requested data or result; logs, progress and
  warnings go to `stderr`.
- `--no-input` never asks a question; missing information is a documented
  error. A missing TTY never makes a command hang.
- Arguments are validated before computation or download starts.
- Subprocesses are called with argument lists, never by concatenating shell
  strings; paths with spaces and Unicode are tested.
- Help, progress, warnings and errors are translated into English, German,
  Spanish and Turkish. Command names, option names, JSON field names and
  error codes are never translated.
- Empty result, missing data and error are distinct outcomes. The tool
  version and the output schema version are separate fields. Large
  genomic data is referenced (path, format, size, checksum), not embedded
  in JSON.
- Error object: at least `code`, `message`, `retryable` and, when needed,
  `details`. Secrets and raw sensitive data never appear in messages.
- Proposed exit codes (final table to be fixed with the first shared CLI
  library): `0` success, `2` invalid usage or input, `3` missing dependency,
  `4` data validation error, `5` network or external service error, `6`
  computation error, `7` blocked by permission or policy.
- Output is completed atomically; overwriting an existing file needs an
  explicit option. Side-effecting operations offer `--dry-run`. Network
  downloads, deletion, installation and uploads are separate, explicit
  permissions. Long jobs react to cancellation and never present partial
  output as complete.
- An LLM interface (for example MCP) may be added later but is never the only
  way to use a tool. Giving an agent access is not giving it root; analyses
  run with user privileges, and text found in files or external data is
  never executed as an instruction.

## Release model

- Versions below 1.0 are unnamed development snapshots; 1.0 is "Bruno", 2.0
  is "Rumi".
- Three identifiers are kept apart: the distribution version (`VERSION`), the
  ISO build identity (distinguishes a rebuilt medium of the same version),
  and each Erik package's own Debian version.
- Development builds use zstd; `--release` builds use xz.
- ISOs, `SHA256SUMS`, audit reports and package manifests are published on
  GitHub Releases, never committed. Planned for 1.0: signed `SHA256SUMS`, a
  GPL source ISO with each release, and builds on a clean CI runner.
