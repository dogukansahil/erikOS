# Wallpapers

The JPEG files in this directory are wallpapers for Erik OS. All current images are center cropped without upscaling to the largest shared 16:9 canvas, 3072 × 1728 pixels. They were saved at JPEG quality 100. Their embedded EXIF, XMP, IPTC, comments, color profile, and other JPEG APP metadata are removed.

## Creator Attribution
All wallpapers are photographed by **Doğukan Sahil**.
Portfolio: https://500px.com/p/dogukansahil

## Wallpaper Geolocation Coordinates
| Wallpaper File | Identifier / Title | Approximate location (latitude, longitude, about 1 km) | Location |
| :--- | :--- | :--- | :--- |
| `mountain.jpg` | Mountain | `37.52, 29.72` | Salda Gölü, Burdur |
| `lake.jpg` | Lake | `37.52, 29.72` | Salda Gölü, Burdur |
| `dragon.jpg` | Dragon | `36.60, 30.50` | Kemer, Antalya |
| `dark.jpg` | Dark | `41.90, 12.47` | Castel Sant'Angelo, Roma |
| `sky.jpg` | Sky | `41.89, 12.49` | Kolezyum, Roma |
| `beach.jpg` | Beach | `36.87, 30.65` | Konyaaltı Sahili, Antalya |
| `pen.jpg` | Blueprint | `40.87, 29.32` | Tuzla, İstanbul |
| `lens.jpg` | Lens | `40.87, 29.32` | Tuzla, İstanbul |

## Processing
To prepare new JPEG wallpapers, first recalculate the largest 16:9 size that fits all images without upscaling, then center crop them to that common size. Run `python3 scripts/strip-wallpaper-metadata.py` from the repository root after cropping. The script removes metadata without further recompression and compares decoded pixels before replacing each file. `python3 scripts/strip-wallpaper-metadata.py --check` reports remaining metadata.
