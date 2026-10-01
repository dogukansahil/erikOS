# Security policy

## Reporting a vulnerability

Please report security problems **privately**, not in public issues or pull
requests.

- Email: dogukansahil@gmail.com
- Once this repository is public, use GitHub's private vulnerability
  reporting (the "Report a vulnerability" button in the Security tab).

Include what you found, the Erik OS version, and steps to reproduce. You
will get an answer as soon as possible; this is a small project, so please
be patient.

## Supported versions

Erik OS is a series of development snapshots before 1.0. **Only the latest
development snapshot is considered, and no security support is promised
before 1.0.** Do not use these snapshots for sensitive data or production
systems. A support policy with supported versions and end dates will be
published with 1.0.

Erik OS is based on Debian; security updates of Debian packages come from
Debian through APT. Erik is responsible for the Erik packages only.

## Archive signing key

Erik packages are distributed in a signed APT archive. The archive signing
key ("Erik OS Archive Signing Key"):

- Type: ed25519
- Fingerprint: `D9FF 82ED 2A05 7CC0 CE3C 5A9E BB7B 7BA3 3F67 D4CC`
- Expires: 2029-09-30

The public key ships in the `erik-archive-keyring` package. The private key
is kept on the release machine, outside this repository, and is never
committed. Protecting it with a passphrase and an offline backup is planned
before the archive is published. If you find a
different fingerprint presented as Erik's, do not trust it and tell us.

## What the ISO audit guarantees

Every ISO is checked by `scripts/audit-iso.py` after the build, and an ISO
that fails is not released. The audit checks that:

- every installed package is the exact version in Debian's signed `main`
  index, or an Erik package;
- every packaged file is unchanged (dpkg checksums) and no file is left
  without an owning package;
- no private keys, local secrets, build machine names, local paths,
  passwords or user accounts leaked into the image;
- APT sources and the files at the root of the ISO are as expected.

The auditor itself is tested (`scripts/tests/test-audit-iso.sh`). The audit
does not prove that the software is free of vulnerabilities, only that the
image contains what it should and nothing else. It does not replace a
security review, which is planned before 1.0.
