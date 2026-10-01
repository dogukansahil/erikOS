# Contributing to Erik OS

Thank you for your interest. Erik OS is early in development; please open an
issue to discuss larger changes before writing code.

## License rule

- Everything you write for Erik OS is licensed **GPL-3.0-only**. Every
  source file starts with an SPDX header, for example
  `SPDX-License-Identifier: GPL-3.0-only` in the comment syntax of the file's
  language. Every package has a `debian/copyright` that declares
  `GPL-3.0-only`.
- Third-party software comes only from Debian **`main`**. No `contrib`,
  `non-free`, `non-free-firmware`, proprietary drivers, foreign repositories,
  downloads of binaries or vendored blobs.
- Artwork you contribute must be your own work and be released under
  GPL-3.0-only.
- A different license for a file needs a written decision in
  `docs/decisions/` first.

The full policy is [`docs/LICENSING.md`](docs/LICENSING.md). The build stops
when it is violated.

## Design rules

- **Every change is a package.** Anything Erik installs on a system is a
  Debian package under `packages/`, so installed systems get it through
  `apt upgrade`. Do not add loose files to the ISO configuration for
  anything that has a lasting purpose.
- **Never edit another package's files.** Use GSettings override files,
  `dpkg-divert` (restored when the package is removed) or
  `update-alternatives`. The ISO audit checks every Debian file byte for
  byte.
- **Four languages.** All user-facing text (installer, system, Erik tools,
  documentation for users) must be available in English, German, Spanish and
  Turkish. Command names, option names, JSON field names and exit codes are
  stable and are never translated.
- **Command line first.** Erik tools must be fully usable from the command
  line, with machine-readable (JSON) output; see
  [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Style

- Text files use LF line endings and UTF-8. The package build refuses CRLF.
- Do not use the em dash character. Use commas, colons, semicolons or
  parentheses.
- Keep documentation concise and accurate; do not claim what is not tested.

## Build and test

Set up a Debian 13 build system as described in
[`docs/BUILDING.md`](docs/BUILDING.md), then run:

```sh
python3 scripts/check-licenses.py          # license and SPDX check
sh scripts/build-packages.sh               # builds packages, runs lintian
sh scripts/build-iso.sh desktop            # or: server; includes the ISO audit
sh scripts/tests/test-audit-iso.sh <iso>   # only when you change the audit
python3 scripts/check-repo.py              # before every commit
```

- `lintian` errors fail a package build; fix them, do not suppress them
  without a reason.
- `scripts/check-repo.py` scans for secrets and leaks (private keys, user
  names, machine names, local paths). Run it before every commit.
- An ISO whose audit (`scripts/audit-iso.py`) fails is not released. If you
  change the audit, run its test, which plants known problems into an ISO
  and must catch all of them.
- Ideally test the ISO by installing it in a virtual machine and say what
  you tested in the pull request.

## Commits and branches

- One topic per commit. Subject line: short, imperative, no trailing period
  (for example `Add erik-theme reset command`). Explain why in the body when
  it is not obvious.
- Use a branch per topic (`fix-installer-focus`, `add-erik-settings`) and
  open a pull request against `main`.
- Never commit ISOs, build output, the `build-environment/` directory or any
  key material.

## Releasing a version

1. Update `VERSION`, the version badge at the top of `README.md` (checked by
   `scripts/check-repo.py`), `CHANGELOG.md` and the versions in the Erik
   packages that changed.
2. Build with `sh scripts/build-iso.sh --release all`; both audits must pass.
3. Tag the commit (`v0.5`) and publish the ISOs, `SHA256SUMS`, audit reports
   and manifests on GitHub Releases.

## Add a new package

See [`packages/README.md`](packages/README.md) ("Add a new tool").

## Security

Do not report vulnerabilities in public issues; see
[`SECURITY.md`](SECURITY.md).
