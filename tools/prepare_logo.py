#!/usr/bin/env python3
"""Prépare un logo monochrome sur fond blanc pour un usage web.

Recadre au plus juste, remplace le fond blanc par de la transparence en
dérivant l'alpha de la luminance (les anti-aliasings restent propres), puis
produit deux versions à plat : une pour les fonds clairs, une pour les fonds
sombres.

    python3 tools/prepare_logo.py source.png assets/img/logo-wordmark
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import png


def luminance(r, g, b):
    return (r * 299 + g * 587 + b * 114) // 1000


def ink_bounds(w, h, px, threshold=225):
    x0, y0, x1, y1 = w, h, -1, -1
    for y in range(h):
        row = y * w
        for x in range(w):
            i = (row + x) * 4
            if luminance(px[i], px[i + 1], px[i + 2]) < threshold:
                if x < x0: x0 = x
                if x > x1: x1 = x
                if y < y0: y0 = y
                if y > y1: y1 = y
    if x1 < 0:
        raise SystemExit("aucun pixel d'encre détecté")
    return x0, y0, x1, y1


def ink_colour(w, h, px, threshold=110):
    tot = [0, 0, 0]
    n = 0
    for i in range(0, w * h):
        j = i * 4
        r, g, b = px[j], px[j + 1], px[j + 2]
        if luminance(r, g, b) < threshold:
            tot[0] += r; tot[1] += g; tot[2] += b; n += 1
    return tuple(c // n for c in tot) if n else (16, 31, 60)


def alpha_mask(w, h, px, box, floor_lum):
    """Alpha = opacité de l'encre, 0 sur le fond blanc, 255 sur le trait plein."""
    x0, y0, x1, y1 = box
    cw, ch = x1 - x0 + 1, y1 - y0 + 1
    span = max(1, 255 - floor_lum)
    mask = bytearray(cw * ch)
    for y in range(ch):
        src = (y + y0) * w
        dst = y * cw
        for x in range(cw):
            i = (src + x + x0) * 4
            lum = luminance(px[i], px[i + 1], px[i + 2])
            a = (255 - lum) * 255 // span
            mask[dst + x] = 255 if a > 255 else (0 if a < 0 else a)
    return cw, ch, mask


def downsample(w, h, mask, target_w):
    """Réduction par moyenne de zone ; conserve la douceur des contours."""
    if target_w >= w:
        return w, h, mask
    ratio = w / target_w
    tw, th = target_w, max(1, round(h / ratio))
    out = bytearray(tw * th)
    for y in range(th):
        sy0, sy1 = int(y * ratio), min(h, max(int(y * ratio) + 1, int((y + 1) * ratio)))
        for x in range(tw):
            sx0, sx1 = int(x * ratio), min(w, max(int(x * ratio) + 1, int((x + 1) * ratio)))
            total = count = 0
            for yy in range(sy0, sy1):
                row = yy * w
                for xx in range(sx0, sx1):
                    total += mask[row + xx]; count += 1
            out[y * tw + x] = total // count if count else 0
    return tw, th, out


def flatten(w, h, mask, colour, pad):
    """Compose un RVBA d'une seule couleur, avec une marge transparente."""
    pw, ph = w + pad * 2, h + pad * 2
    r, g, b = colour
    px = bytearray(pw * ph * 4)
    for y in range(h):
        dst = ((y + pad) * pw + pad) * 4
        src = y * w
        for x in range(w):
            a = mask[src + x]
            if a:
                j = dst + x * 4
                px[j] = r; px[j + 1] = g; px[j + 2] = b; px[j + 3] = a
    return pw, ph, px


def main():
    source, stem = sys.argv[1], sys.argv[2]
    target_w = int(sys.argv[3]) if len(sys.argv) > 3 else 1200

    w, h, px = png.read(source)
    box = ink_bounds(w, h, px)
    colour = ink_colour(w, h, px)
    floor = luminance(*colour)
    cw, ch, mask = alpha_mask(w, h, px, box, floor)
    print(f"source        : {w} × {h}")
    print(f"encre         : #{colour[0]:02x}{colour[1]:02x}{colour[2]:02x}")
    print(f"recadrage     : {cw} × {ch}  (marges retirées : "
          f"{box[0]} g, {box[1]} h, {w-1-box[2]} d, {h-1-box[3]} b)")

    cw, ch, mask = downsample(cw, ch, mask, target_w)
    pad = max(2, round(ch * 0.04))

    for suffix, rgb in ((".png", colour), ("-light.png", (255, 255, 255))):
        pw, ph, out = flatten(cw, ch, mask, rgb, pad)
        path = Path(f"{stem}{suffix}")
        path.parent.mkdir(parents=True, exist_ok=True)
        size = png.write(str(path), pw, ph, out)
        print(f"écrit         : {path}  {pw} × {ph}  {size/1024:.0f} Ko")


if __name__ == "__main__":
    main()
