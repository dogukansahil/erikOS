#!/usr/bin/env python3
"""Remove JPEG metadata without recompressing wallpaper image data."""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
WALLPAPERS = ROOT / "assets" / "wallpapers"
METADATA_MARKERS = set(range(0xE0, 0xF0)) | {0xFE}  # APP0..APP15 and COM
STANDALONE_MARKERS = {0x01, 0xD8, 0xD9} | set(range(0xD0, 0xD8))


def strip_segments(data: bytes) -> tuple[bytes, list[str], int]:
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("not a JPEG file")
    output = bytearray(data[:2])
    removed: list[str] = []
    position = 2

    while position < len(data):
        start = position
        if data[position] != 0xFF:
            raise ValueError(f"invalid JPEG marker at offset {position}")
        while position < len(data) and data[position] == 0xFF:
            position += 1
        if position >= len(data):
            raise ValueError("truncated JPEG marker")
        marker = data[position]
        position += 1
        if marker == 0x00:
            raise ValueError("unexpected byte stuffing outside JPEG scan")
        if marker == 0xD9:
            output.extend(data[start:position])
            return bytes(output), removed, len(data) - position
        if marker in STANDALONE_MARKERS:
            output.extend(data[start:position])
            continue
        if position + 2 > len(data):
            raise ValueError("truncated JPEG segment length")
        length = int.from_bytes(data[position : position + 2], "big")
        if length < 2 or position + length > len(data):
            raise ValueError("invalid JPEG segment length")
        end = position + length
        if marker in METADATA_MARKERS:
            removed.append("COM" if marker == 0xFE else f"APP{marker - 0xE0}")
        else:
            output.extend(data[start:end])
        position = end

        if marker == 0xDA:  # Start of scan; preserve entropy-coded data exactly.
            scan_start = position
            while True:
                marker_start = data.find(b"\xff", position)
                if marker_start < 0:
                    raise ValueError("JPEG scan has no ending marker")
                probe = marker_start + 1
                while probe < len(data) and data[probe] == 0xFF:
                    probe += 1
                if probe >= len(data):
                    raise ValueError("truncated JPEG scan marker")
                next_marker = data[probe]
                if next_marker == 0x00 or 0xD0 <= next_marker <= 0xD7:
                    position = probe + 1
                    continue
                output.extend(data[scan_start:marker_start])
                position = marker_start
                break
    raise ValueError("JPEG has no end marker")


def pixel_fingerprint(data: bytes) -> tuple[tuple[int, int], str, str, int]:
    with Image.open(io.BytesIO(data)) as image:
        orientation = image.getexif().get(274, 1)
        image.load()
        return image.size, image.mode, hashlib.sha256(image.tobytes()).hexdigest(), orientation


def process(path: Path, check_only: bool) -> bool:
    initial = path.stat()
    original = path.read_bytes()
    cleaned, removed, trailing = strip_segments(original)
    if not removed and not trailing:
        print(f"clean: {path.name}")
        return False
    if check_only:
        print(f"metadata remains: {path.name} ({len(removed)} segments, {trailing} trailing bytes)")
        return True

    before = pixel_fingerprint(original)
    if before[3] != 1:
        raise ValueError(f"{path.name}: EXIF orientation {before[3]} needs visual normalization first")
    after = pixel_fingerprint(cleaned)
    if before[:3] != after[:3]:
        raise ValueError(f"{path.name}: decoded pixels changed; original retained")
    if path.stat().st_mtime_ns != initial.st_mtime_ns or path.stat().st_size != initial.st_size:
        raise ValueError(f"{path.name}: file changed during processing; original retained")

    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.stem}-", suffix=".jpg.tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(cleaned)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f"stripped: {path.name} ({len(removed)} segments, {len(original) - len(cleaned)} bytes removed)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report remaining metadata without changing files")
    args = parser.parse_args()
    files = sorted(path for path in WALLPAPERS.iterdir() if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg"})
    if not files:
        parser.error(f"no JPEG wallpapers found in {WALLPAPERS}")
    changed = False
    for path in files:
        changed |= process(path, args.check)
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
