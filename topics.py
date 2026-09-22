# -*- coding: utf-8 -*-
"""日本のポケカ情報を英語で1日1本Instagramに投稿する（出品投稿とは別枠）。

ネタの優先順位:
  1. topics.json の未投稿エントリ（新商品ニュース優先。英文はあらかじめ用意しておく）
  2. 無ければ「日本の相場ウォッチ」を eBay/メルカリの実データから自動生成

画像は自前で描画する（他人の写真・公式画像は使わない＝権利問題を避ける）。

使い方:
  python topics.py --dry-run   投稿せず画像とキャプションだけ作る
  python topics.py             実投稿
  python topics.py --news      公式サイトの新着ニュースを表示（topics.json補充用・投稿はしない）
"""
import truststore
truststore.inject_into_ssl()

import html
import json
import os
import re
import sys
import textwrap
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

import insta_post as ip

BASE = Path(__file__).parent
IMAGES = BASE / "topic_images"
TOPICS = BASE / "topics.json"
POSTED = BASE / "topics_posted.json"
JST = timezone(timedelta(hours=9))

NEWS_URL = "https://www.pokemon-card.com/info/"
UA = {"User-Agent": "Mozilla/5.0"}

BG = (18, 20, 28)
FG = (245, 246, 250)
ACCENT = (255, 203, 5)      # ポケモンイエロー寄り
SUB = (150, 157, 175)

HASHTAGS = ("#pokemoncards #pokemontcg #pokemonjapan #japanesepokemoncards #pokemonnews "
            "#ポケカ #ポケモンカード #pokemoncardgame #tcgnews #pokemoncollector "
            "#vintagepokemon #pokemonpromo #tcg #cardcollector")


# ---------- 公式ニュース（topics.json を補充するときの参照用） ----------
def fetch_news(limit=20):
    t = requests.get(NEWS_URL, timeout=30, headers=UA).text
    pat = (r'<li class="List_item">\s*<a class="List_item_inner" href="([^"]+)".*?'
           r'<div class="Calendar_Label[^"]*">([^<]*)</div>\s*([^<]+?)\s*'
           r'<span class="Date Date-small">([^<]+)</span>')
    out = []
    for url, label, title, date in re.findall(pat, t, re.S)[:limit]:
        if url.startswith("/"):
            url = "https://www.pokemon-card.com" + url
        out.append({"date": date.strip(), "category": label.strip(),
                    "title_ja": html.unescape(title.strip()), "url": url})
    return out


# ---------- 相場ウォッチ（ネタ切れ時の自動生成） ----------
WATCH_CARDS = [
    ("Pikachu Gold Star 001/002", "Pikachu Gold Star 001/002 Japanese", "ピカチュウ☆ 001/002", "001/002"),
    ("Mewtwo Gold Star 002/002", "Mewtwo Gold Star 002/002 Japanese", "ミュウツー☆ 002/002", "002/002"),
    ("Umbreon Gold Star 024/PLAY", "Umbreon Gold Star 024/PLAY Japanese", "ブラッキー☆ 024/PLAY", "024/play"),
    ("Charizard 103/128 e-Card", "Charizard 103/128 Japanese e-card holo 1st edition", "リザードン 103/128", "103/128"),
    ("Lugia No.249 Neo Genesis", "Lugia Neo Genesis Japanese holo old back", "旧裏 ルギア neo", "ルギア"),
    ("Latias Gold Star 065/082", "Latias Gold Star 065/082 Japanese", "ラティアス☆ 065/082", "065/082"),
]


def market_topic():
    """eBayの現在最安（日本セラー）を3枚分集めて相場ウォッチのネタにする。"""
    import ebay_search_shim as es
    rows = []
    for label, eq, _jq, must in WATCH_CARDS:
        try:
            r = es.competition(eq, [must] if "/" in must else [], es.EXCLUDE)
        except Exception:
            continue
        if r.get("jp_lowest"):
            rows.append((label, r["jp_lowest"], r["total"]))
        time.sleep(1.5)
        if len(rows) >= 3:
            break
    if not rows:
        return None
    today = datetime.now(JST).strftime("%b %d")
    return {
        "id": "market-" + datetime.now(JST).strftime("%Y%m%d"),
        "kind": "market",
        "headline": "Japan Market Watch",
        "sub": today,
        "bullets": ["{}  —  ${:,.0f}  ({} listings)".format(a, b, c) for a, b, c in rows],
        "caption": ("Japan Market Watch 🇯🇵 ({})\n\n".format(today)
                    + "\n".join("▶ {} — lowest from a Japanese seller: ${:,.0f} ({} active listings)".format(a, b, c)
                                for a, b, c in rows)
                    + "\n\nPrices are the lowest currently listed by sellers in Japan on eBay, checked today."
                      "\nI ship these straight from Japan — DM me if you're hunting for one. 😊"),
    }


# ---------- 画像生成 ----------
def _font(size, bold=False):
    cands = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for c in cands:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def make_image(topic):
    IMAGES.mkdir(exist_ok=True)
    out = IMAGES / "{}.jpg".format(topic["id"])
    W, H = 1080, 1350
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    # 上下のアクセントバー
    d.rectangle([0, 0, W, 14], fill=ACCENT)
    d.rectangle([0, H - 14, W, H], fill=ACCENT)

    y = 120
    d.text((80, y), topic.get("kicker", "JAPAN POKÉMON TCG").upper(), font=_font(30, True), fill=ACCENT)
    y += 60

    for line in textwrap.wrap(topic["headline"], width=20)[:4]:
        d.text((80, y), line, font=_font(76, True), fill=FG)
        y += 92

    if topic.get("sub"):
        y += 10
        d.text((80, y), topic["sub"], font=_font(34), fill=SUB)
        y += 70

    y = max(y + 30, 620)
    for b in topic.get("bullets", [])[:5]:
        d.ellipse([84, y + 16, 100, y + 32], fill=ACCENT)
        for i, line in enumerate(textwrap.wrap(b, width=34)[:3]):
            d.text((124, y), line, font=_font(38), fill=FG)
            y += 50
        y += 26

    # 絵文字はフォントに無く豆腐になるので画像には入れない（キャプション側で使う）
    d.text((80, H - 118), "@fancy_tcg_japan", font=_font(34, True), fill=ACCENT)
    d.text((80, H - 74), "Japanese cards, shipped from Japan", font=_font(28), fill=SUB)
    im.save(out, "JPEG", quality=92)
    return out


# ---------- main ----------
def pick_topic(posted):
    if TOPICS.exists():
        queue = json.loads(TOPICS.read_text(encoding="utf-8"))
        # 新商品（product）を優先し、次に古い順
        pending = [t for t in queue if t["id"] not in posted]
        pending.sort(key=lambda t: (0 if t.get("kind") == "product" else 1, t.get("order", 999)))
        if pending:
            return pending[0]
    return market_topic()


def main():
    if "--news" in sys.argv:
        for n in fetch_news():
            print(n["date"], "|", n["category"], "|", n["title_ja"], "|", n["url"])
        return

    dry = "--dry-run" in sys.argv
    posted = json.loads(POSTED.read_text(encoding="utf-8")) if POSTED.exists() else {}
    topic = pick_topic(posted)
    if not topic:
        print("投稿するネタがありません（topics.json が空で相場取得も失敗）")
        return

    path = make_image(topic)
    caption = topic["caption"].rstrip() + "\n\n" + HASHTAGS
    (BASE / "last_topic_caption.txt").write_text(caption, encoding="utf-8")
    print("topic:", topic["id"], "->", path.name)
    if dry:
        print("\n--- caption ---\n" + caption)
        return

    repo = os.environ.get("IMAGE_REPO_RAW", "")
    if not repo:
        raise SystemExit("IMAGE_REPO_RAW が未設定です")
    import ig_token
    token = ig_token.get_token()
    me = ip.ig_get("me", fields="user_id,username", access_token=token)[1]
    uid = me.get("user_id") or me.get("id")
    if not uid:
        raise RuntimeError("Instagram user_id が取れません: {}".format(me))
    url = "{}/topic_images/{}.jpg".format(repo, topic["id"])
    c = ip.ig_post("{}/media".format(uid), image_url=url, caption=caption, access_token=token)
    if not ip.wait_container(c["id"], token):
        raise RuntimeError("container not ready: {}".format(c))
    r = ip.ig_post("{}/media_publish".format(uid), creation_id=c["id"], access_token=token)
    posted[topic["id"]] = {"headline": topic["headline"],
                           "posted_at": datetime.now(JST).isoformat(timespec="minutes"),
                           "media_id": r.get("id")}
    POSTED.write_text(json.dumps(posted, ensure_ascii=False, indent=2), encoding="utf-8")
    print("投稿完了 media_id={}".format(r.get("id")))


if __name__ == "__main__":
    main()
