"""Lecture et écriture de PNG en Python pur (zlib de la bibliothèque standard).

Suffisant pour les besoins du projet : profondeur 8 bits, non entrelacé,
niveaux de gris, palette, RVB et RVBA.
"""

import struct
import zlib

SIGNATURE = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def read(path):
    """Retourne (largeur, hauteur, pixels RVBA sous forme de bytearray)."""
    raw = open(path, "rb").read()
    if raw[:8] != SIGNATURE:
        raise ValueError("ce fichier n'est pas un PNG")

    pos, idat, palette, trns = 8, [], None, None
    width = height = depth = color = None
    while pos < len(raw):
        length = struct.unpack(">I", raw[pos : pos + 4])[0]
        kind = raw[pos + 4 : pos + 8]
        data = raw[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, depth, color, _, _, interlace = struct.unpack(">IIBBBBB", data)
            if depth != 8 or interlace:
                raise ValueError(f"PNG non pris en charge (profondeur {depth}, entrelacé {interlace})")
        elif kind == b"PLTE":
            palette = data
        elif kind == b"tRNS":
            trns = data
        elif kind == b"IDAT":
            idat.append(data)
        elif kind == b"IEND":
            break

    n = CHANNELS[color]
    stride = width * n
    lines = zlib.decompress(b"".join(idat))
    flat = _unfilter(lines, width, height, n, stride)
    return width, height, _to_rgba(flat, width, height, n, color, palette, trns)


def _unfilter(data, width, height, n, stride):
    out = bytearray(height * stride)
    prev = bytearray(stride)
    pos = 0
    for y in range(height):
        ftype = data[pos]
        pos += 1
        line = bytearray(data[pos : pos + stride])
        pos += stride
        if ftype == 1:
            for i in range(n, stride):
                line[i] = (line[i] + line[i - n]) & 0xFF
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:
            for i in range(stride):
                left = line[i - n] if i >= n else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:
            for i in range(stride):
                a = line[i - n] if i >= n else 0
                b = prev[i]
                c = prev[i - n] if i >= n else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 0xFF
        elif ftype != 0:
            raise ValueError(f"filtre PNG inconnu : {ftype}")
        out[y * stride : (y + 1) * stride] = line
        prev = line
    return out


def _to_rgba(flat, width, height, n, color, palette, trns):
    px = bytearray(width * height * 4)
    for i in range(width * height):
        s, d = i * n, i * 4
        if color == 0:
            g = flat[s]; px[d:d+4] = bytes((g, g, g, 255))
        elif color == 4:
            g = flat[s]; px[d:d+4] = bytes((g, g, g, flat[s+1]))
        elif color == 2:
            px[d:d+3] = flat[s:s+3]; px[d+3] = 255
        elif color == 6:
            px[d:d+4] = flat[s:s+4]
        elif color == 3:
            k = flat[s] * 3
            px[d:d+3] = palette[k:k+3]
            px[d+3] = trns[flat[s]] if trns and flat[s] < len(trns) else 255
    return px


def write(path, width, height, rgba):
    """Écrit un PNG RVBA (couleur 6, profondeur 8)."""
    stride = width * 4
    raw = bytearray()
    for y in range(height):
        raw.append(0)                                  # filtre « aucun »
        raw += rgba[y * stride : (y + 1) * stride]

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    body = (SIGNATURE
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))
    open(path, "wb").write(body)
    return len(body)
