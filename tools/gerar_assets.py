"""Gera a arte do Arena Real (personagens, torres, arena, UI). Rode: python tools/gerar_assets.py"""
import math, os, random
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')
S = 4
OL = (38, 24, 48, 255)


def cv(n):
    img = Image.new('RGBA', (n * S, n * S), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img), n * S


class P:
    def __init__(s, n):
        s.img, s.d, s.N = cv(n)

    def f(s, v):
        return v * s.N

    def ell(s, cx, cy, rx, ry, fill, ol=OL, w=2.2):
        s.d.ellipse([s.f(cx - rx), s.f(cy - ry), s.f(cx + rx), s.f(cy + ry)], fill=fill,
                    outline=ol, width=int(w * S) if ol else 0)

    def rr(s, x0, y0, x1, y1, r, fill, ol=OL, w=2.2):
        s.d.rounded_rectangle([s.f(x0), s.f(y0), s.f(x1), s.f(y1)], radius=s.f(r), fill=fill,
                              outline=ol, width=int(w * S) if ol else 0)

    def poly(s, pts, fill, ol=OL, w=2.2):
        pp = [(s.f(x), s.f(y)) for x, y in pts]
        s.d.polygon(pp, fill=fill)
        if ol:
            s.d.line(pp + [pp[0]], fill=ol, width=int(w * S), joint='curve')

    def line(s, pts, fill, w=2.5):
        s.d.line([(s.f(x), s.f(y)) for x, y in pts], fill=fill, width=int(w * S), joint='curve')

    def shadow(s, cx=.5, cy=.9, rx=.3, ry=.06):
        s.d.ellipse([s.f(cx - rx), s.f(cy - ry), s.f(cx + rx), s.f(cy + ry)], fill=(0, 0, 0, 70))

    def eyes(s, y=.33, dx=.065, r=.028, col=(30, 20, 40, 255)):
        for sx in (-1, 1):
            s.ell(.5 + sx * dx, y, r, r * 1.3, (255, 255, 255, 255), None)
            s.ell(.5 + sx * dx, y + .004, r * .6, r * .8, col, None)

    def done(s, size):
        return s.img.resize((size, size), Image.LANCZOS)


SKIN = (255, 214, 170, 255)


def cavaleiro():
    p = P(128); p.shadow()
    for x in (.38, .56):
        p.rr(x, .78, x + .1, .89, .03, (60, 45, 70, 255))
    p.rr(.3, .46, .7, .8, .08, (62, 112, 225, 255))
    p.rr(.3, .64, .7, .7, .02, (240, 190, 60, 255))
    p.poly([(.12, .48), (.34, .48), (.34, .68), (.23, .82), (.12, .68)], (52, 84, 190, 255))
    p.ell(.23, .62, .045, .045, (245, 200, 70, 255))
    p.poly([(.75, .16), (.8, .2), (.81, .6), (.72, .6)], (215, 225, 240, 255))
    p.rr(.67, .59, .86, .65, .02, (245, 200, 70, 255))
    p.rr(.73, .65, .79, .75, .02, (120, 70, 40, 255))
    p.ell(.7, .56, .06, .06, SKIN)
    p.ell(.5, .3, .19, .18, (190, 202, 220, 255))
    p.ell(.5, .35, .125, .1, SKIN, None)
    p.eyes(.345, .06, .026)
    p.rr(.34, .27, .66, .3, .01, (110, 120, 145, 255), None)
    p.poly([(.5, .1), (.66, .02), (.6, .17)], (230, 60, 60, 255))
    return p.done(128)


def arqueiras():
    p = P(128); p.shadow()
    p.poly([(.32, .46), (.68, .46), (.75, .84), (.25, .84)], (66, 170, 96, 255))
    p.rr(.3, .6, .7, .66, .02, (140, 90, 50, 255))
    p.ell(.5, .3, .22, .22, (56, 150, 82, 255))
    p.ell(.5, .33, .15, .15, SKIN)
    p.ell(.5, .21, .17, .08, (255, 125, 190, 255), None)
    for sx in (-1, 1):
        p.ell(.5 + sx * .15, .38, .04, .1, (255, 125, 190, 255))
    p.eyes(.34, .06, .026)
    p.d.arc([p.f(.62), p.f(.28), p.f(.94), p.f(.82)], -80, 80, fill=(130, 80, 40, 255), width=6 * S)
    cx, cy, rx, ry = .78, .55, .16, .27
    ex = cx + rx * math.cos(math.radians(80)); ey = ry * math.sin(math.radians(80))
    p.line([(ex, cy - ey), (ex, cy + ey)], (240, 240, 240, 255), 1)
    p.line([(.3, .55), (.82, .55)], (200, 160, 100, 255), 1.6)
    p.poly([(.82, .52), (.9, .55), (.82, .58)], (220, 225, 235, 255), None)
    p.ell(.34, .56, .05, .05, SKIN)
    return p.done(128)


def gigante():
    p = P(128); p.shadow(rx=.36)
    p.rr(.3, .74, .7, .9, .04, (110, 70, 50, 255))
    p.rr(.18, .4, .82, .8, .14, (232, 172, 122, 255))
    p.poly([(.28, .42), (.72, .42), (.66, .78), (.34, .78)], (140, 85, 50, 255))
    p.rr(.34, .62, .66, .68, .02, (240, 190, 60, 255))
    for sx in (-1, 1):
        p.ell(.5 + sx * .38, .62, .1, .1, (232, 172, 122, 255))
    p.ell(.5, .38, .17, .13, (240, 125, 40, 255))
    p.ell(.5, .27, .14, .13, (232, 172, 122, 255))
    p.ell(.5, .17, .16, .06, (240, 125, 40, 255), None)
    p.eyes(.27, .06, .022)
    for sx in (-1, 1):
        p.line([(.5 + sx * .1, .205), (.5 + sx * .03, .23)], OL, 1.6)
    p.line([(.45, .34), (.55, .34)], OL, 1.5)
    return p.done(128)


def goblins():
    p = P(128); p.shadow(rx=.25)
    for sx in (-1, 1):
        p.poly([(.5 + sx * .2, .36), (.5 + sx * .46, .2), (.5 + sx * .3, .46)], (112, 200, 74, 255))
    p.rr(.38, .78, .62, .9, .03, (90, 60, 40, 255))
    p.ell(.5, .68, .15, .15, (150, 100, 55, 255))
    p.ell(.5, .38, .22, .2, (112, 200, 74, 255))
    for sx in (-1, 1):
        p.ell(.5 + sx * .09, .34, .05, .06, (255, 240, 120, 255))
        p.ell(.5 + sx * .09, .345, .02, .035, OL, None)
    p.poly([(.47, .38), (.53, .38), (.5, .46)], (90, 170, 60, 255), None)
    p.rr(.4, .47, .6, .54, .03, (60, 30, 40, 255))
    for x in (.44, .54):
        p.poly([(x, .47), (x + .03, .47), (x + .015, .51)], (255, 255, 240, 255), None)
    p.poly([(.76, .5), (.8, .5), (.8, .72), (.78, .76), (.76, .72)], (215, 225, 240, 255), None, 0)
    p.line([(.78, .5), (.78, .74)], (215, 225, 240, 255), 2.2)
    return p.done(128)


def mago():
    p = P(128); p.shadow()
    p.poly([(.3, .45), (.7, .45), (.8, .9), (.2, .9)], (240, 120, 42, 255))
    p.rr(.2, .84, .8, .9, .02, (170, 70, 30, 255))
    p.poly([(.38, .42), (.62, .42), (.5, .74)], (250, 250, 250, 255))
    p.ell(.5, .33, .13, .12, SKIN)
    p.eyes(.325, .055, .022)
    p.ell(.5, .3, .26, .06, (170, 70, 30, 255))
    p.poly([(.3, .3), (.7, .3), (.6, .1), (.54, .02), (.5, .1)], (240, 120, 42, 255))
    p.ell(.5, .2, .035, .035, (255, 230, 80, 255), None)
    p.line([(.84, .2), (.84, .9)], (130, 80, 40, 255), 3)
    for r, c in ((.11, (80, 200, 255, 120)), (.07, (130, 225, 255, 255)), (.035, (255, 255, 255, 255))):
        p.ell(.84, .18, r, r, c, OL if r == .07 else None)
    p.ell(.7, .56, .06, .06, SKIN)
    return p.done(128)


def barbaros():
    p = P(128); p.shadow()
    p.rr(.36, .78, .64, .9, .03, (120, 80, 50, 255))
    p.rr(.28, .46, .72, .8, .1, (236, 178, 120, 255))
    p.poly([(.28, .72), (.72, .72), (.76, .84), (.24, .84)], (160, 100, 60, 255))
    p.rr(.28, .66, .72, .72, .02, (240, 190, 60, 255))
    p.ell(.5, .3, .17, .17, SKIN)
    p.poly([(.28, .3), (.3, .55), (.38, .42), (.5, .52), (.62, .42), (.7, .55), (.72, .3), (.5, .1)],
           (250, 215, 80, 255))
    p.ell(.5, .33, .12, .11, SKIN, None)
    p.eyes(.315, .055, .022)
    for sx in (-1, 1):
        p.ell(.5 + sx * .06, .405, .07, .03, (250, 215, 80, 255))
    p.ell(.5, .17, .17, .06, (190, 195, 205, 255))
    for sx in (-1, 1):
        p.poly([(.5 + sx * .15, .17), (.5 + sx * .3, .06), (.5 + sx * .22, .22)], (245, 240, 225, 255))
    p.line([(.82, .2), (.82, .74)], (130, 80, 40, 255), 4.5)
    p.ell(.82, .2, .07, .09, (150, 95, 55, 255))
    p.ell(.74, .55, .06, .06, SKIN)
    return p.done(128)


def esqueletos():
    p = P(128); p.shadow(rx=.22)
    W = (242, 242, 232, 255)
    for sx in (-1, 1):
        p.line([(.5 + sx * .08, .72), (.5 + sx * .1, .88)], W, 3)
        p.line([(.5 + sx * .17, .5), (.5 + sx * .26, .64)], W, 2.6)
    p.rr(.38, .46, .62, .74, .06, W)
    for y in (.52, .58, .64, .7):
        p.line([(.41, y), (.59, y)], OL, 1.2)
    p.ell(.5, .3, .19, .17, W)
    for sx in (-1, 1):
        p.ell(.5 + sx * .075, .3, .045, .055, (25, 15, 35, 255), None)
    p.poly([(.47, .37), (.53, .37), (.5, .32)], (25, 15, 35, 255), None)
    p.rr(.4, .4, .6, .46, .02, W)
    for x in (.45, .5, .55):
        p.line([(x, .4), (x, .46)], OL, 1)
    p.line([(.8, .3), (.8, .72)], W, 3.4)
    p.ell(.8, .3, .035, .035, W)
    return p.done(128)


def fogo():
    p = P(128)
    p.poly([(.1, .9), (.3, .4), (.42, .55), (.5, .3), (.62, .5), (.78, .72)], (255, 120, 30, 200), None)
    p.ell(.55, .52, .3, .3, (255, 100, 25, 255))
    p.ell(.55, .54, .21, .21, (255, 170, 40, 255), None)
    p.ell(.55, .56, .12, .12, (255, 240, 150, 255), None)
    for a in range(0, 360, 45):
        x = .55 + .33 * math.cos(math.radians(a)); y = .52 + .33 * math.sin(math.radians(a))
        p.ell(x, y, .04, .05, (255, 200, 60, 255), None)
    return p.done(128)


def stone_bricks(p, x0, y0, x1, y1, base, rows=6, cols=4, seed=1):
    r = random.Random(seed)
    for i in range(rows):
        yy0 = y0 + (y1 - y0) * i / rows; yy1 = y0 + (y1 - y0) * (i + 1) / rows
        off = (i % 2) * .5
        for j in range(-1, cols + 1):
            xx0 = x0 + (x1 - x0) * (j + off) / cols; xx1 = x0 + (x1 - x0) * (j + off + 1) / cols
            xx0, xx1 = max(xx0, x0), min(xx1, x1)
            if xx1 - xx0 < .01:
                continue
            sh = r.randint(-10, 10)
            c = (base[0] + sh, base[1] + sh, base[2] + sh, 255)
            p.rr(xx0 + .004, yy0 + .004, xx1 - .004, yy1 - .004, .01, c, (80, 80, 100, 255), 1.0)


def torre(team, rei):
    col = (62, 112, 225, 255) if team == 0 else (232, 66, 66, 255)
    dark = (40, 78, 170, 255) if team == 0 else (170, 40, 40, 255)
    p = P(256)
    p.shadow(.5, .93, .38 if rei else .3, .05)
    if rei:
        for sx in (-1, 1):
            p.rr(.5 + sx * .36 - .1, .5, .5 + sx * .36 + .1, .9, .03, (170, 170, 185, 255))
            stone_bricks(p, .5 + sx * .36 - .09, .52, .5 + sx * .36 + .09, .88, (160, 160, 178), 4, 2, 3)
            p.poly([(.5 + sx * .36 - .13, .52), (.5 + sx * .36 + .13, .52), (.5 + sx * .36, .34)], col)
        p.rr(.24, .36, .76, .93, .04, (176, 176, 192, 255))
        stone_bricks(p, .25, .38, .75, .91, (170, 170, 188), 7, 4, 5)
        for i in range(5):
            p.rr(.22 + i * .1, .28, .22 + i * .1 + .07, .38, .01, (186, 186, 202, 255))
        p.rr(.42, .66, .58, .93, .08, (90, 56, 40, 255))
        p.rr(.38, .5, .62, .58, .02, col)
        p.ell(.5, .54, .03, .03, (250, 220, 90, 255), None)
        p.poly([(.34, .3), (.4, .14), (.45, .24), (.5, .08), (.55, .24), (.6, .14), (.66, .3)], (250, 205, 60, 255))
        p.rr(.34, .27, .66, .33, .015, (240, 180, 40, 255))
        for x, c in ((.4, (255, 80, 110, 255)), (.5, (90, 200, 255, 255)), (.6, (255, 80, 110, 255))):
            p.ell(x, .3, .018, .018, c, None)
    else:
        p.rr(.28, .42, .72, .93, .04, (176, 176, 192, 255))
        stone_bricks(p, .29, .44, .71, .91, (170, 170, 188), 6, 3, 7)
        for i in range(4):
            p.rr(.26 + i * .12, .34, .26 + i * .12 + .08, .44, .01, (188, 188, 204, 255))
        p.rr(.42, .72, .58, .93, .07, (90, 56, 40, 255))
        p.poly([(.36, .5), (.64, .5), (.64, .66), (.5, .72), (.36, .66)], col)
        p.ell(.5, .58, .035, .035, (250, 220, 90, 255), None)
        p.ell(.5, .26, .09, .09, SKIN)
        p.ell(.5, .21, .12, .06, dark)
        p.poly([(.4, .22), (.6, .22), (.5, .08)], col)
        p.eyes(.27, .035, .014)
        p.line([(.64, .3), (.82, .2)], (130, 80, 40, 255), 2.2)
    return p.done(256)


def ruinas():
    p = P(256); r = random.Random(4)
    p.shadow(.5, .85, .36, .07)
    for _ in range(16):
        x = .5 + r.uniform(-.28, .28); y = .8 - r.uniform(0, .2) * (1 - abs(x - .5) * 2)
        c = r.randint(120, 175)
        s = r.uniform(.04, .09)
        p.poly([(x - s, y), (x - s * .4, y - s), (x + s, y - s * .6), (x + s * .8, y + s * .3)], (c, c, c + 12, 255), OL, 1.6)
    return p.done(256)


def coroa(cor=(250, 205, 60, 255)):
    p = P(96)
    p.poly([(.1, .78), (.06, .3), (.3, .5), (.5, .16), (.7, .5), (.94, .3), (.9, .78)], cor)
    p.rr(.1, .74, .9, .9, .04, tuple(max(0, c - 40) for c in cor[:3]) + (255,))
    for x, c in ((.25, (255, 80, 110, 255)), (.5, (90, 200, 255, 255)), (.75, (255, 80, 110, 255))):
        p.ell(x, .82, .045, .045, c, None)
    return p.done(96)


def gota():
    p = P(96)
    p.poly([(.5, .06), (.78, .5), (.82, .66), (.7, .84), (.5, .92), (.3, .84), (.18, .66), (.22, .5)], (190, 70, 245, 255))
    p.ell(.5, .66, .3, .26, (190, 70, 245, 255), None)
    p.ell(.38, .6, .07, .11, (235, 190, 255, 220), None)
    return p.done(96)


def arena():
    W, H = 720, 1280
    r = random.Random(7)
    img = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(img)
    RIOY = (640 - 320) * 2
    for y in range(0, H, 80):
        for x in range(0, W, 80):
            alt = ((x // 80) + (y // 80)) % 2
            top = y < RIOY
            base = (68, 142, 64) if top else (82, 166, 80)
            c = tuple(v + (7 if alt else 0) for v in base)
            d.rectangle([x, y, x + 80, y + 80], fill=c)
    for _ in range(900):
        x, y = r.randint(0, W), r.randint(0, H)
        if abs(y - RIOY) < 70:
            continue
        c = (52, 118, 50) if y < RIOY else (62, 140, 62)
        d.line([x, y, x - 3, y - 8], fill=c, width=2); d.line([x, y, x + 3, y - 8], fill=c, width=2)
    for _ in range(70):
        x, y = r.randint(20, W - 20), r.randint(20, H - 20)
        if abs(y - RIOY) < 80:
            continue
        col = r.choice([(255, 240, 120), (255, 255, 255), (255, 150, 190)])
        for a in range(0, 360, 90):
            d.ellipse([x + 4 * math.cos(math.radians(a)) - 2, y + 4 * math.sin(math.radians(a)) - 2,
                       x + 4 * math.cos(math.radians(a)) + 2, y + 4 * math.sin(math.radians(a)) + 2], fill=col)
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(240, 180, 40))
    for cx in (180, 540):
        for y0, y1 in ((RIOY + 70, 1040), (240, RIOY - 70)):
            d.rounded_rectangle([cx - 34, min(y0, y1), cx + 34, max(y0, y1)], radius=30, fill=(190, 160, 110))
            d.rounded_rectangle([cx - 28, min(y0, y1) + 6, cx + 28, max(y0, y1) - 6], radius=26, fill=(205, 176, 124))
    for i, (cx, cy, sz) in enumerate([(180, 1040, 64), (540, 1040, 64), (360, 1160, 80),
                                        (180, 240, 64), (540, 240, 64), (360, 120, 80)]):
        d.rounded_rectangle([cx - sz, cy - sz, cx + sz, cy + sz], radius=22, fill=(140, 140, 156), outline=(80, 80, 100), width=4)
        d.rounded_rectangle([cx - sz + 8, cy - sz + 8, cx + sz - 8, cy + sz - 8], radius=16, fill=(168, 168, 184))
        for k in range(-sz + 24, sz - 8, 26):
            d.line([cx + k, cy - sz + 10, cx + k, cy + sz - 10], fill=(145, 145, 162), width=2)
            d.line([cx - sz + 10, cy + k, cx + sz - 10, cy + k], fill=(145, 145, 162), width=2)
    for yy in (RIOY - 56, RIOY + 56):
        d.rectangle([0, yy - 14, W, yy + 14], fill=(226, 205, 150))
        d.rectangle([0, yy - 14 if yy < RIOY else yy + 8, W, yy - 8 if yy < RIOY else yy + 14], fill=(190, 168, 118))
    for y in range(RIOY - 46, RIOY + 46):
        t = (y - (RIOY - 46)) / 92
        d.line([0, y, W, y], fill=(int(70 + 20 * math.sin(t * 3.14)), int(150 + 20 * math.sin(t * 3.14)), 235))
    for _ in range(60):
        x = r.randint(0, W); y = r.randint(RIOY - 38, RIOY + 38)
        d.arc([x, y, x + 34, y + 10], 200, 340, fill=(190, 230, 255), width=2)
    for _ in range(25):
        x = r.randint(0, W); y = r.randint(RIOY - 40, RIOY + 40)
        d.ellipse([x, y, x + 4, y + 4], fill=(255, 255, 255))
    for cx in (180, 540):
        d.rectangle([cx - 66, RIOY - 62, cx + 66, RIOY + 62], fill=(150, 104, 58))
        for y in range(RIOY - 60, RIOY + 62, 16):
            d.rectangle([cx - 60, y, cx + 60, y + 13], fill=(194, 142, 84), outline=(120, 80, 44))
        for sx in (-1, 1):
            d.rectangle([cx + sx * 60 - (6 if sx > 0 else 0), RIOY - 66, cx + sx * 60 + (0 if sx > 0 else 6) + (6 if sx > 0 else 0), RIOY + 66], fill=(110, 72, 40))
            for yy in (RIOY - 62, RIOY + 62):
                d.ellipse([cx + sx * 63 - 9, yy - 9, cx + sx * 63 + 9, yy + 9], fill=(130, 88, 48), outline=(80, 50, 28), width=2)
    for side in (0, 1):
        for _ in range(26):
            y = r.randint(0, H)
            if abs(y - RIOY) < 70:
                continue
            x = r.randint(0, 14) if side == 0 else W - r.randint(0, 14)
            rad = r.randint(14, 24)
            g = r.randint(0, 25)
            d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(36 + g, 98 + g, 44 + g), outline=(26, 70, 34))
            d.ellipse([x - rad // 2, y - rad // 2 - 4, x, y - 2], fill=(70 + g, 140 + g, 76 + g))
    return img.filter(ImageFilter.SMOOTH)


def gradient(w, h, c0, c1, linha=None):
    img = Image.new('RGBA', (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        d.line([0, y, w, y], fill=tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3)) + (255,))
    return img, d


def painel():
    img, d = gradient(720, 240, (52, 40, 92), (20, 15, 40))
    for x in range(-240, 720, 36):
        d.line([x, 240, x + 240, 0], fill=(255, 255, 255, 10), width=8)
    d.rectangle([0, 0, 720, 7], fill=(236, 190, 70))
    d.rectangle([0, 7, 720, 10], fill=(150, 100, 30))
    return img


def topbar():
    img, d = gradient(720, 60, (34, 26, 66), (16, 12, 34))
    d.rectangle([0, 56, 720, 60], fill=(236, 190, 70))
    return img


def menu_bg():
    W, H = 720, 1280
    img, d = gradient(W, H, (96, 60, 170), (250, 150, 110))
    r = random.Random(3)
    for _ in range(90):
        x, y = r.randint(0, W), r.randint(0, int(H * .55))
        s = r.choice((1, 1, 2, 3))
        d.ellipse([x, y, x + s, y + s], fill=(255, 255, 255, r.randint(120, 255)))
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for k in range(14):
        a0 = k * 25.7
        od.pieslice([W // 2 - 900, 360 - 900, W // 2 + 900, 360 + 900], a0, a0 + 9, fill=(255, 235, 170, 30))
    img.alpha_composite(ov)
    d = ImageDraw.Draw(img)
    for cx, cy, s in ((120, 330, 1.0), (590, 250, .8), (430, 440, .7)):
        for dx, dy, rr_ in ((0, 0, 46), (50, 14, 38), (-48, 16, 34), (20, 24, 40)):
            d.ellipse([cx + dx * s - rr_ * s, cy + dy * s - rr_ * s * .6, cx + dx * s + rr_ * s, cy + dy * s + rr_ * s * .6],
                      fill=(255, 255, 255, 255))
    base = [(0, 1280), (0, 1020), (90, 1020), (90, 940), (120, 940), (120, 880), (150, 940), (150, 1000), (260, 1000),
            (260, 900), (360, 820), (460, 900), (460, 1000), (570, 1000), (570, 940), (600, 880), (630, 940),
            (630, 1020), (720, 1020), (720, 1280)]
    d.polygon(base, fill=(40, 26, 70, 255))
    for x, y in ((360, 930), (170, 1040), (550, 1040), (360, 1030)):
        d.rounded_rectangle([x - 12, y - 18, x + 12, y + 18], radius=10, fill=(255, 210, 110, 255))
    d.rectangle([0, 1130, W, H], fill=(52, 120, 56))
    for x in range(0, W, 36):
        d.rectangle([x, 1130, x + 18, H], fill=(58, 130, 62))
    return img


def sheet(imgs, nome):
    w = sum(i.width for i in imgs) + 10 * (len(imgs) + 1)
    sh = Image.new('RGBA', (w, max(i.height for i in imgs) + 20), (90, 150, 90, 255))
    x = 10
    for i in imgs:
        sh.alpha_composite(i, (x, 10)); x += i.width + 10
    sh.save(nome)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    chars = dict(cavaleiro=cavaleiro(), arqueiras=arqueiras(), gigante=gigante(), goblins=goblins(),
                 mago=mago(), barbaros=barbaros(), esqueletos=esqueletos(), fogo=fogo())
    for k, v in chars.items():
        v.save(os.path.join(OUT, k + '.png'))
    for team, nm in ((0, 'b'), (1, 'r')):
        torre(team, False).save(os.path.join(OUT, 'torre_%s.png' % nm))
        torre(team, True).save(os.path.join(OUT, 'rei_%s.png' % nm))
    ruinas().save(os.path.join(OUT, 'ruinas.png'))
    coroa().save(os.path.join(OUT, 'coroa.png'))
    coroa((120, 120, 130, 255)).save(os.path.join(OUT, 'coroa_off.png'))
    gota().save(os.path.join(OUT, 'gota.png'))
    arena().save(os.path.join(OUT, 'arena.png'))
    painel().save(os.path.join(OUT, 'painel.png'))
    topbar().save(os.path.join(OUT, 'topbar.png'))
    menu_bg().convert('RGB').save(os.path.join(OUT, 'menu_bg.png'))
    if os.environ.get('SHEET'):
        sheet(list(chars.values()) + [torre(0, False), torre(1, True), ruinas()], '/home/claude/w/sheet.png')
    print('ok')
