"""Generate a 128x128 PNG app icon without extra dependencies."""
import struct
import zlib
from pathlib import Path


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_icon(path, rgb):
    size = 128
    raw = bytearray()
    r, g, b = rgb
    for y in range(size):
        raw.append(0)
        for x in range(size):
            margin = 10
            inner = margin <= x < size - margin and margin <= y < size - margin
            if inner:
                raw.extend((r, g, b, 255))
            else:
                raw.extend((36, 36, 48, 255))
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _chunk(b"IEND", b"")
    )


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    write_icon(here / "icon.png", (47, 111, 145))
