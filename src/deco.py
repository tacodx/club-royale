"""Art-deco Monte Carlo style system: black, gold, burgundy."""
import os, math
import numpy as np
from paths import ASSETS
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = str(ASSETS)
os.makedirs(OUT, exist_ok=True)
SC = 2

INK   = (9, 8, 11)
INK2  = (22, 18, 24)
INK3  = (38, 30, 40)
BURG  = (86, 17, 32)
FELT  = (104, 22, 40)
BURG_D= (32, 7, 14)
BURG_L= (140, 32, 50)
GOLD  = (201, 162, 39)
GOLD_L= (240, 216, 140)
GOLD_D= (122, 94, 24)
CREAM = (242, 233, 214)
GREY  = (128, 116, 122)

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FS = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
_fc = {}


def font(size, f=FB):
    if (size, f) not in _fc:
        _fc[(size, f)] = ImageFont.truetype(f, int(size))
    return _fc[(size, f)]


def new(w, h):
    return Image.new("RGBA", (int(w * SC), int(h * SC)), (0, 0, 0, 0))


def save(img, name):
    p = os.path.join(OUT, name + ".png")
    img.save(p)
    return p


# ------------------------------------------------------------- gold fill
def gold_fill(mask, vertical=True, light=GOLD_L, mid=GOLD, dark=GOLD_D):
    """Fill a mask with a metallic gold gradient."""
    w, h = mask.size
    grad = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(grad)
    n = h if vertical else w
    for i in range(n):
        t = i / max(1, n - 1)
        # dark -> light -> mid  (a soft metallic sweep)
        if t < 0.45:
            u = t / 0.45
            c = tuple(int(dark[j] + (light[j] - dark[j]) * u) for j in range(3))
        else:
            u = (t - 0.45) / 0.55
            c = tuple(int(light[j] + (mid[j] - light[j]) * u) for j in range(3))
        if vertical:
            d.line([(0, i), (w, i)], fill=c + (255,))
        else:
            d.line([(i, 0), (i, h)], fill=c + (255,))
    grad.putalpha(mask.split()[3] if mask.mode == "RGBA" else mask)
    return grad


def chamfer_pts(box, cut):
    x0, y0, x1, y1 = box
    return [(x0 + cut, y0), (x1 - cut, y0), (x1, y0 + cut), (x1, y1 - cut),
            (x1 - cut, y1), (x0 + cut, y1), (x0, y1 - cut), (x0, y0 + cut)]


def deco_panel(size, fill=BURG_D, cut=None, rule=True, width=3, inner=True,
               alpha=255, rule_col=None):
    """Chamfered (octagonal) panel with a gold double rule."""
    w, h = int(size[0]), int(size[1])
    cut = cut if cut is not None else int(min(w, h) * 0.13)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = chamfer_pts([2, 2, w - 3, h - 3], cut)
    if fill:
        d.polygon(pts, fill=fill + (alpha,))
    if rule:
        line = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ld = ImageDraw.Draw(line)
        ld.polygon(pts, outline=(255, 255, 255, 255), width=width)
        if inner:
            ic = max(2, int(cut * 0.62))
            ld.polygon(chamfer_pts([2 + width * 2.6, 2 + width * 2.6,
                                    w - 3 - width * 2.6, h - 3 - width * 2.6], ic),
                       outline=(255, 255, 255, 210), width=max(1, width // 2))
        img = Image.alpha_composite(
            img, gold_fill(line) if rule_col is None
            else _flat(line, rule_col))
    return img


def _flat(mask, col):
    g = Image.new("RGBA", mask.size, col + (0,))
    g.putalpha(mask.split()[3])
    return g


def tracked(img, xy, text, size, tracking=None, color=None, f=FB,
            anchor="mm", gold=True):
    """Letter-spaced capitals - the deco signature."""
    fnt = font(size, f)
    tracking = tracking if tracking is not None else size * 0.18
    widths = [fnt.getlength(ch) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x, y = xy
    if anchor[0] == "m": x -= total / 2
    elif anchor[0] == "r": x -= total
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for ch, cw in zip(text, widths):
        ld.text((x, y), ch, font=fnt, fill=(255, 255, 255, 255),
                anchor="l" + anchor[1])
        x += cw + tracking
    img.alpha_composite(gold_fill(lay) if gold else _flat(lay, color or CREAM))
    return total


def sunburst(size, cx, cy, rays=48, length=900, col=GOLD, alpha=26, spread=1.0):
    w, h = size
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(rays):
        a = (i / rays) * 2 * math.pi * spread - math.pi / 2
        wob = 2 * math.pi / rays * 0.30
        p1 = (cx + math.cos(a - wob) * length, cy + math.sin(a - wob) * length)
        p2 = (cx + math.cos(a + wob) * length, cy + math.sin(a + wob) * length)
        d.polygon([(cx, cy), p1, p2], fill=col + (alpha,))
    return lay


def radial_mask(size, cx, cy, r_in, r_out, power=1.4):
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    t = np.clip((dist - r_in) / max(1e-6, (r_out - r_in)), 0, 1)
    return Image.fromarray((255 * (1 - t) ** power).astype("uint8"), "L")


def vignette(img, strength=200, r_in=0.30, r_out=1.02, power=1.7):
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w]
    dx = (xx - w / 2) / (w / 2)
    dy = (yy - h / 2) / (h / 2)
    dist = np.sqrt(dx ** 2 + dy ** 2) / 1.414
    t = np.clip((dist - r_in) / (r_out - r_in), 0, 1) ** power
    dark = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dark.putalpha(Image.fromarray((strength * t).astype("uint8"), "L"))
    return Image.alpha_composite(img, dark)


def hairline(img, y, x0, x1, gap=5, w1=3, w2=1):
    """Deco double rule."""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.line([(x0, y), (x1, y)], fill=(255, 255, 255, 255), width=w1)
    d.line([(x0, y + gap + w1), (x1, y + gap + w1)],
           fill=(255, 255, 255, 190), width=w2)
    img.alpha_composite(gold_fill(lay))


def chevron(img, cx, cy, w, h, n=3, step=5, up=True, col=GOLD, alpha=170):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(n):
        o = i * step
        s = 1 if up else -1
        d.line([(cx - w, cy + o * s + h * s), (cx, cy + o * s),
                (cx + w, cy + o * s + h * s)],
               fill=col + (alpha,), width=3, joint="curve")
    img.alpha_composite(lay)


# ============================================================== backdrop
def backdrop(name="bg"):
    W, H = 480 * SC, 360 * SC
    img = Image.new("RGBA", (W, H), INK + (255,))

    # overhead spotlight
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([W * 0.5 - 560, -460, W * 0.5 + 560, 640],
                                fill=(64, 52, 44, 80))
    img = Image.alpha_composite(img, lay.filter(ImageFilter.GaussianBlur(160)))

    # the table
    tw, th = 448 * SC, 262 * SC
    tx, ty = (W - tw) // 2, int(43 * SC)
    tbl = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    pts = chamfer_pts([0, 0, tw - 1, th - 1], 24 * SC)
    ImageDraw.Draw(tbl).polygon(pts, fill=BURG_D + (255,))
    # lit felt centre
    lay = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([tw * 0.10, -th * 0.06, tw * 0.90, th * 1.06],
                                fill=FELT + (255,))
    lay.putalpha(Image.fromarray(
        (np.asarray(lay.split()[3]).astype(float) *
         np.asarray(radial_mask((tw, th), tw / 2, th / 2,
                                th * 0.05, th * 0.78, 1.2)) / 255
         ).astype("uint8")))
    tbl = Image.alpha_composite(tbl, lay.filter(ImageFilter.GaussianBlur(70)))
    # inlaid deco sunburst medallion
    rays = sunburst((tw, th), tw / 2, th / 2, rays=32, length=700, alpha=13)
    rays.putalpha(Image.fromarray(
        (np.asarray(rays.split()[3]).astype(float) *
         np.asarray(radial_mask((tw, th), tw / 2, th / 2,
                                24, th * 0.52, 2.2)) / 255).astype("uint8")))
    tbl = Image.alpha_composite(tbl, rays)
    # faint gold lattice on the felt
    lat = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lat)
    step = 34 * SC
    for i in range(-th // step, tw // step + 2):
        ld.line([(i * step, 0), (i * step + th, th)], fill=GOLD + (12,), width=1)
        ld.line([(i * step, th), (i * step + th, 0)], fill=GOLD + (12,), width=1)
    tbl = Image.alpha_composite(tbl, lat)
    tbl = vignette(tbl, strength=165, r_in=0.34, r_out=1.05)
    # re-cut the chamfer after vignetting
    cut = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(cut).polygon(pts, fill=255)
    tbl.putalpha(Image.fromarray(
        (np.asarray(tbl.split()[3]).astype(float) *
         np.asarray(cut) / 255).astype("uint8")))
    # gold double rule
    line = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.polygon(pts, outline=(255, 255, 255, 255), width=3)
    ld.polygon(chamfer_pts([10 * SC, 10 * SC, tw - 1 - 10 * SC, th - 1 - 10 * SC],
                           17 * SC), outline=(255, 255, 255, 130), width=1)
    tbl = Image.alpha_composite(tbl, gold_fill(line))
    img.alpha_composite(tbl, (tx, ty))

    # bars
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 34 * SC], fill=INK + (255,))
    d.rectangle([0, H - 44 * SC, W, H], fill=INK + (255,))
    hairline(img, 34 * SC, 0, W)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).line([(0, H - 44 * SC), (W, H - 44 * SC)],
                             fill=(255, 255, 255, 255), width=3)
    ImageDraw.Draw(lay).line([(0, H - 44 * SC - 8), (W, H - 44 * SC - 8)],
                             fill=(255, 255, 255, 140), width=1)
    img.alpha_composite(gold_fill(lay))

    tracked(img, (16 * SC, 17 * SC), "CHIPS", 11 * SC, anchor="lm")
    return save(img, name)


if __name__ == "__main__":
    backdrop()
    print("ok")
