"""v7 additions: arcade cabinet support.

Two pieces of art, both in the house style:

- the focus frame the joystick moves between controls. One costume per
  distinct control size, generated on demand by build.py from the sizes of the
  costumes it frames, so the frame cannot drift from the thing it surrounds.
- the OUT OF CHIPS banner a cabinet shows in place of the green flag it does
  not have.

The frame is a ring: everything inside the control's own box is fully
transparent. Scratch picks the sprite under a click by its pixels, not its
bounding box, so a hollow frame drawn on top of a button never takes the
button's clicks. `focus_frame` asserts that rather than trusting it.
"""
from deco import *
from assets_v11 import fit, panel
import os
from PIL import Image, ImageDraw

MARGIN = 4          # stage units between the control's edge and the frame
STROKE = 2.5        # stage units, the gold rule itself


def focus_frame(w, h, rounded=False):
    """Frame for a w x h (stage units) control. Returns the costume name."""
    w, h = int(round(w)), int(round(h))
    name = f"focus_{'r' if rounded else 'c'}{w}x{h}"
    if os.path.exists(os.path.join(OUT, name + ".png")):
        return name
    pad = MARGIN + STROKE + 2
    img = new(w + 2 * pad, h + 2 * pad)
    W, H = img.size
    o = (pad - MARGIN - STROKE) * SC          # outer edge of the rule
    box = [o, o, W - 1 - o, H - 1 - o]
    sw = int(STROKE * SC)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd, ld = ImageDraw.Draw(shadow), ImageDraw.Draw(line)
    if rounded:
        sd.ellipse([b + (-1 if i < 2 else 1) for i, b in enumerate(box)],
                   outline=(8, 4, 8, 200), width=sw + 4)
        ld.ellipse(box, outline=(255, 255, 255, 255), width=sw)
    else:
        cut = 5 * SC      # small enough to clear the control's own corners
        sd.polygon(chamfer_pts(box, cut), outline=(8, 4, 8, 200), width=sw + 4)
        ld.polygon(chamfer_pts(box, cut), outline=(255, 255, 255, 255), width=sw)
    img = Image.alpha_composite(img, shadow)
    img = Image.alpha_composite(
        img, gold_fill(line, light=(255, 244, 200), mid=GOLD_L, dark=GOLD))
    # the control itself must stay clear, or the frame would eat its clicks
    body = Image.new("L", (W, H), 0)
    x0, y0 = pad * SC, pad * SC
    (ImageDraw.Draw(body).ellipse if rounded else ImageDraw.Draw(body).rectangle)(
        [x0, y0, W - 1 - x0, H - 1 - y0], fill=255)
    from PIL import ImageChops
    covered = ImageChops.multiply(img.split()[3], body)
    assert covered.getextrema()[1] == 0, f"{name}: frame is not hollow"
    save(img, name)
    return name


BANNER_W, BANNER_H = 300, 46


def broke_banner():
    img, (W, H) = panel(BANNER_W, BANNER_H, cut=12 * SC,
                        fill=(58, 11, 22, 255), inner=6, width=3)
    s, tr = fit("OUT OF CHIPS", 15 * SC, 4 * SC, W - 40 * SC)
    tracked(img, (W / 2, 17 * SC), "OUT OF CHIPS", s, tr, anchor="mm")
    sub = "PRESS START FOR A FRESH 1,000"
    s, tr = fit(sub, 8 * SC, 2 * SC, W - 40 * SC)
    tracked(img, (W / 2, 33 * SC), sub, s, tr, anchor="mm",
            color=CREAM, gold=False)
    save(img, "broke_banner")


def build():
    broke_banner()


if __name__ == "__main__":
    build()
    print("arcade assets ok ->", OUT)
