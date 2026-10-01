# Erik OS license policy

Erik OS is distributed to the public. Every file we ship must be free to
redistribute, and nothing in the image may expose users or Genotomi to a
copyright, license or trademark claim. These rules are binding for every
release, every edition and every contributor.

## Rule 1: everything Erik writes is GPL-3.0-only

All original Erik OS work is licensed under the GNU General Public License,
version 3 only (SPDX: `GPL-3.0-only`). This covers:

- every `erik-*` package (`packages/`) and every Erik tool (kept in the
  separate `erikos-tools` repository until it is packaged),
- build scripts, live-build configuration and hooks (`editions/`, `scripts/`),
- the Erik APT archive configuration (`archive/`),
- installer branding and configuration,
- artwork: wallpapers, logo and theme files (decided 2026-10-01; the
  photographs are original work of the project maintainer).

Each source file starts with `SPDX-License-Identifier: GPL-3.0-only`. Each
package has a machine-readable `debian/copyright` declaring `GPL-3.0-only`
and nothing else. "GPL-3.0-or-later", dual licensing, or a different license
for one file needs a written decision in `docs/decisions/` first.

## Rule 2: third-party software comes only from Debian `main`

Software we did not write is taken unmodified from Debian's `main` archive
area, which contains only software that meets the Debian Free Software
Guidelines.

- Allowed archive area: `main`. Not allowed: `contrib`, `non-free`,
  `non-free-firmware` (decided 2026-10-01).
- No third-party APT repositories, PPAs, Flatpak remotes, binary downloads,
  `curl | sh` installers or vendored blobs in the image.
- No proprietary drivers or runtimes, for example NVIDIA drivers or CUDA.
  GPU support is limited to what Debian `main` provides.
- No proprietary fonts, codecs or firmware.

Consequence: some Wi-Fi cards and GPUs need firmware that is not in `main`
and will not work out of the box. If firmware is ever offered, it will be a
separate, clearly labelled, opt-in step that the user chooses; it is never
part of the default image.

## Rule 2a: opt-in proprietary drivers (planned, decided 2026-10-01)

Erik Settings will offer NVIDIA drivers and CUDA as an **opt-in** action on
an installed system, because GPU computing matters for life sciences. This
does not break Rule 2, because Erik never distributes them:

- Nothing proprietary is ever in the ISO, the Erik repository or an Erik
  package. Erik ships only the free settings tool that performs the steps.
- The user starts it, sees which vendor and license are involved, and
  accepts NVIDIA's license in the tool before anything is downloaded.
- The software comes from the vendor's official source (NVIDIA's CUDA
  repository, or Debian's `non-free` area for the driver), enabled only for
  that purpose, with the vendor's signing key pinned to that source.
- Updates arrive through APT from that source; the tool can remove the
  driver, CUDA and the added source again, leaving no trace.
- The installed system shows that it now contains non-free software.

The same pattern applies to any future opt-in proprietary component, and
each one needs its own decision record first.

## Rule 3: no foreign branding

Erik OS is based on Debian but is not Debian. Unmodified Debian packages may
be redistributed, but the product must never present itself with Debian's,
GNOME's or another project's name or logo as if it were theirs.

- System identity comes from `erik-base` (`/usr/lib/os-release`: `ID=erik`,
  `ID_LIKE=debian`). "Based on Debian" is fine as a description.
- Default artwork comes from `erik-theme`. Debian and GNOME wallpaper lists
  are hidden with `dpkg-divert`, never edited or deleted.
- Remaining Debian-branded surfaces (boot menu, Plymouth, server console,
  text installer of the server edition) are tracked in `ROADMAP.md` and
  must be replaced before 1.0.

## Rule 4: data and external services

NCBI records, publications, reference genomes and other data keep their own
terms. Tools that download data must not bundle it in the image, must show
the source, and must not suggest an endorsement (for example, a tool that
uses NCBI services must state that it is independent and not affiliated
with NCBI).

## Enforcement

`scripts/check-licenses.py` runs at the start of every package build
(`scripts/build-packages.sh`) and every ISO build
(`scripts/build-iso.sh`). It stops the build when:

- an Erik package declares a license other than `GPL-3.0-only`,
- an Erik source file lacks the SPDX header,
- an edition enables an archive area other than `main`,
- a package list names a known non-free package.

`lintian --fail-on error` checks every package. `scripts/audit-iso.py`
then opens every finished ISO and checks that each installed package is the
exact version in Debian's signed `main` index or an Erik package (see
[`BUILDING.md`](BUILDING.md)). A build that fails these checks is not released, and
the checks are not bypassed.

The GPL-3.0 text is in the repository root `LICENSE`. Installed systems
point to `/usr/share/common-licenses/GPL-3`.
