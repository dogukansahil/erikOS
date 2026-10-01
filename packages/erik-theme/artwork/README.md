# Erik artwork

`logo.png` (500 × 500, transparent) is the single source of the Erik logo.
Replace it when the logo changes and keep the file name. Everything else is
derived from it:

| Output | Made by | Used for |
|---|---|---|
| `/usr/share/erik/artwork/logo.png`, `/usr/share/pixmaps/erik-logo.png` | `erik-theme` package (`debian/install`, `debian/links`) | Icons of Erik apps and launchers |
| `vendor-logos/` (logo with "Erik OS", PNG and SVG, 64/128/256 px) | `make-vendor-logos.py` (python3-pil, fonts-cantarell) | GDM login screen and other vendor logo users, through the `vendor-logos` alternative |
| `../../erik-base/files/erik-logo.txt`, `erik-logo-fastfetch.txt` | `make-ascii-logo.py` (python3-pil) | fastfetch, the server login banner, text documents |
| Calamares installer logo in `editions/desktop/config/includes.chroot/etc/calamares/branding/erik/` | `scripts/stage-artwork.py` | The live installer (not part of an installed system) |

After changing `logo.png`, run the two generators and the staging script,
commit their output, and raise the versions of the changed packages:

```sh
python3 packages/erik-theme/artwork/make-vendor-logos.py
python3 packages/erik-theme/artwork/make-ascii-logo.py
python3 scripts/stage-artwork.py
```

The package build does not run the generators, so the committed output is
what ships. Cantarell is licensed under the SIL Open Font License, which
allows its use in images.
