# Erik OS local build environment

Local only. This directory is excluded from Git (only this README is
tracked) and must never be published: it holds virtual disks, the private
archive signing key, caches and the generated APT tree.

## Layout

- `wsl/disk/`: disk of the WSL2 distro `ErikOS-Build` (Debian 13). Builds
  packages and ISOs. Created 2026-10-01.
- `secrets/gnupg/`: private key "Erik OS Archive Signing Key"
  (ed25519, fingerprint `D9FF 82ED 2A05 7CC0 CE3C 5A9E BB7B 7BA3 3F67 D4CC`,
  expires 2029-09-30). Losing it means users must install a new keyring.
  Back it up offline.
- `secrets/reprepro/`: reprepro database of the APT archive.
- `archive-out/apt/`: the generated, signed APT tree written by
  `scripts/publish-repo.sh`. It is published separately from here (never
  committed).
- `virtualbox/ErikOS-Test/`: VirtualBox VM for live boot and installation tests.
- `virtualbox/ErikOS-Build/`: previous VirtualBox build VM (0.1 and 0.2).
  Replaced by WSL; can be deleted.
- `work/`, `outputs/`: early helper scripts, screenshots and archived outputs.

## WSL build distro

Any Debian 13 system works for building (see
[`../docs/BUILDING.md`](../docs/BUILDING.md)). The project's own WSL distro is
installed into this directory so the project folder holds everything:

```powershell
wsl --install Debian --name ErikOS-Build --location "<project>\build-environment\wsl\disk" --no-launch
```

Tools installed as root:

```sh
apt-get install --no-install-recommends live-build debootstrap squashfs-tools \
  xorriso dpkg-dev debhelper devscripts lintian reprepro gnupg fakeroot \
  python3 rsync ca-certificates apt-file build-essential
```

After a Windows reinstall, re-register the existing disk instead of
installing again:

```powershell
wsl --import-in-place ErikOS-Build "<project>\build-environment\wsl\disk\ext4.vhdx"
```

Builds work on the Linux file system (`/root/erik-work`), because the
Windows drive mounted under `/mnt` is slow and makes every file look
executable. The scripts copy sources there themselves.

## VirtualBox test VM

The test VM uses 1 virtual CPU with paravirtualization disabled, because the
original test host showed Linux RCU stalls with more CPUs. Treat it as a host
quirk, not a hardware requirement.
