# -*- coding: utf-8 -*-
"""Sunday Grail（月曜の手作り投稿）のカルーセル画像を作る。

使い方: python grail_post.py 2026-10-19
→ topic_images/grail-20261019-1.jpg ... を出力。スラブ写真は PSA の cert 画像（large）を取得する。
"""
import io, sys, textwrap
from pathlib import Path
import truststore; truststore.inject_into_ssl()
import requests
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "topic_images"
CDN = "https://d1htnxwo4o0jhw.cloudfront.net/cert/"
W, H = 1080, 1350
BG = (18, 20, 28); FG = (245, 246, 250); ACCENT = (255, 203, 5); SUB = (150, 157, 175)

GRAILS = {
    "2026-10-19": {
        "title": "Poncho-wearing Eevee",
        "sub": "Espeon & Umbreon ponchos  ·  2017 Japanese promo",
        "slabs": [
            {"img": "213503238/large/0rOCVFW3kU6RNnuTKRvLMg.jpg", "label": "#140  ESPEON PONCHO",
             "grade": "PSA 9 MINT", "cert": "164581887"},
            {"img": "206325579/large/lL0UrLxvzUqPoC5mioM_ig.jpg", "label": "#141  UMBREON PONCHO",
             "grade": "PSA 8 NM-MT", "cert": "155912804"},
        ],
        "why_title": "Eevee in costume",
        "why": [
            "A 2017 Japanese promo from the Eevee Mega Campaign",
            "Eevee dressed up in Espeon and Umbreon ponchos, a day-and-night pair",
            "Even the attacks play along: \"Psychic?\" and \"Confuse Ray?\"",
            "Illustrated by Kouki Saitou",
            "Both slabs sit in the PSA Vault: vault to vault, nothing ships from Japan",
            "DM me for a price, one or the pair",
        ],
    },
}


def F(s, b=False):
    return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if b else "C:/Windows/Fonts/segoeui.ttf", s)


def base():
    im = Image.new("RGB", (W, H), BG); dr = ImageDraw.Draw(im)
    dr.rectangle([0, 0, W, 14], fill=ACCENT); dr.rectangle([0, H - 14, W, H], fill=ACCENT)
    dr.text((80, H - 118), "@fancy_tcg_japan", font=F(34, True), fill=ACCENT)
    dr.text((80, H - 74), "Japanese cards, shipped from Japan", font=F(28), fill=SUB)
    return im, dr


def fetch(path):
    r = requests.get(CDN + path, timeout=30); r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGB")


def paste_fit(im, img, box):
    x0, y0, x1, y1 = box
    img = img.copy(); img.thumbnail((x1 - x0, y1 - y0), Image.LANCZOS)
    im.paste(img, (x0 + (x1 - x0 - img.width) // 2, y0 + (y1 - y0 - img.height) // 2))


def main(date):
    g = GRAILS[date]; tag = date.replace("-", "")
    imgs = [fetch(s["img"]) for s in g["slabs"]]
    outs = []
    # 1枚目: 全体
    im, dr = base()
    dr.text((80, 100), "SUNDAY GRAIL", font=F(32, True), fill=ACCENT)
    dr.text((80, 145), g["title"], font=F(76, True), fill=FG)
    dr.text((80, 250), g["sub"], font=F(34), fill=SUB)
    n = len(imgs); gap = 40; cw = (W - 160 - gap * (n - 1)) // n
    for i, img in enumerate(imgs):
        x = 80 + i * (cw + gap)
        paste_fit(im, img, (x, 330, x + cw, 1200))
    outs.append(im)
    # 2枚目以降: 1枚ずつ
    for s, img in zip(g["slabs"], imgs):
        im, dr = base()
        dr.text((80, 100), s["grade"], font=F(32, True), fill=ACCENT)
        dr.text((80, 145), s["label"], font=F(52, True), fill=FG)
        dr.text((W - 80, 112), "cert " + s["cert"], font=F(26), fill=SUB, anchor="ra")
        paste_fit(im, img, (80, 230, W - 80, 1200))
        outs.append(im)
    # 最後: 解説
    im, dr = base()
    dr.text((80, 100), "WHY COLLECTORS LOVE IT", font=F(32, True), fill=ACCENT)
    dr.text((80, 145), g["why_title"], font=F(76, True), fill=FG)
    y = 330
    for b in g["why"]:
        dr.ellipse([84, y + 16, 100, y + 32], fill=ACCENT)
        for ln in textwrap.wrap(b, width=42):
            dr.text((124, y), ln, font=F(38), fill=FG); y += 50
        y += 30
    outs.append(im)
    for i, im in enumerate(outs, 1):
        p = OUT / "grail-{}-{}.jpg".format(tag, i)
        im.save(p, "JPEG", quality=92); print(p.name)


if __name__ == "__main__":
    main(sys.argv[1])
