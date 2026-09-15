# -*- coding: utf-8 -*-
"""eBay の自分の出品（新着）を毎日 Instagram にカルーセル投稿する。

流れ:
  1. eBay Browse API で fancy_tcg_japan の出品一覧を取得
  2. posted.json に無い新着を最大10件（新しい順）
  3. 画像を 4:5 (1080x1350) に白背景でパディングして images/ に保存
     （Instagram API は 4:5〜1.91:1 以外を拒否する。eBay写真は 3:4 が多い）
  4. GitHub の raw URL を image_url として Instagram Graph API に渡し、カルーセル投稿
  5. posted.json に記録して二重投稿を防ぐ

使い方:
  python insta_post.py --dry-run   投稿せず画像とキャプションだけ作る
  python insta_post.py             実投稿（環境変数 IG_ACCESS_TOKEN or ig_token.enc が必要）
"""
import truststore
truststore.inject_into_ssl()

import base64
import io
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from PIL import Image

BASE = Path(__file__).parent
IMAGES = BASE / "images"
POSTED = BASE / "posted.json"

SELLER = "fancy_tcg_japan"
MAX_ITEMS = 10
IMAGE_REPO_RAW = os.environ.get("IMAGE_REPO_RAW", "")   # 例: https://raw.githubusercontent.com/<user>/<repo>/main
IG_API = "https://graph.instagram.com/v21.0"
JST = timezone(timedelta(hours=9))

HASHTAGS = ("#pokemoncards #pokemontcg #pokemoncard #japanesepokemoncards #pokemonjapan "
            "#ポケカ #ポケモンカード #goldstar #pokemonpromo #vintagepokemon #pokemoncollector "
            "#ebay #ebayseller #cardcollector #tcg")


# ---------- eBay ----------
def ebay_app_token():
    basic = base64.b64encode("{}:{}".format(os.environ["EBAY_APP_ID"], os.environ["EBAY_CERT_ID"]).encode()).decode()
    r = requests.post("https://api.ebay.com/identity/v1/oauth2/token",
                      headers={"Authorization": "Basic " + basic,
                               "Content-Type": "application/x-www-form-urlencoded"},
                      data={"grant_type": "client_credentials",
                            "scope": "https://api.ebay.com/oauth/api_scope"}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def fetch_listings():
    """自分の出品を Browse API で取得（カテゴリ検索とキーワード検索の和集合）。"""
    tok = ebay_app_token()
    h = {"Authorization": "Bearer " + tok, "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"}
    items = {}
    for params in ({"category_ids": "183454"}, {"category_ids": "261328"}, {"q": "pokemon"}, {"q": "card"}):
        params = dict(params, filter="sellers:{%s}" % SELLER, limit=200)
        r = requests.get("https://api.ebay.com/buy/browse/v1/item_summary/search", headers=h, params=params, timeout=30)
        if r.status_code != 200:
            continue
        for it in r.json().get("itemSummaries", []):
            iid = it["itemId"].split("|")[1]
            items[iid] = {
                "id": iid,
                "title": it["title"],
                "price": float(it["price"]["value"]),
                "url": "https://www.ebay.com/itm/" + iid,
                "image": it["image"]["imageUrl"].replace("s-l225", "s-l1600").replace("s-l500", "s-l1600"),
                "created": it.get("itemCreationDate", ""),
            }
        time.sleep(1)
    return list(items.values())


# ---------- 画像 ----------
def make_image(item):
    """eBay画像を 1080x1350 (4:5) の白背景に収めて保存。返り値は保存パス。"""
    out = IMAGES / "{}.jpg".format(item["id"])
    if out.exists():
        return out
    im = Image.open(io.BytesIO(requests.get(item["image"], timeout=60).content)).convert("RGB")
    W, H = 1080, 1350
    scale = min((W - 80) / im.width, (H - 80) / im.height)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), "white")
    canvas.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
    IMAGES.mkdir(exist_ok=True)
    canvas.save(out, "JPEG", quality=90)
    return out


def caption_for(items):
    today = datetime.now(JST).strftime("%b %d")
    lines = ["New arrivals on eBay 🇯🇵 ({})".format(today), ""]
    for it in items:
        lines.append("▶ {} — ${:,.0f}".format(it["title"], it["price"]))
    lines += ["", "All items ship from Japan with tracking.",
              "eBay store: fancy_tcg_japan (link in bio)", "", HASHTAGS]
    return "\n".join(lines)[:2200]


# ---------- Instagram ----------
def ig_get(path, **params):
    r = requests.get("{}/{}".format(IG_API, path), params=params, timeout=60)
    return r.status_code, r.json()


def ig_post(path, **data):
    r = requests.post("{}/{}".format(IG_API, path), data=data, timeout=60)
    if r.status_code != 200:
        raise RuntimeError("Instagram API error {}: {}".format(r.status_code, r.text[:300]))
    return r.json()


def wait_container(cid, token, max_wait=180):
    for _ in range(max_wait // 5):
        st, d = ig_get(cid, fields="status_code,status", access_token=token)
        if d.get("status_code") == "FINISHED":
            return True
        if d.get("status_code") == "ERROR":
            raise RuntimeError("container error: {}".format(d))
        time.sleep(5)
    return False


def publish(items, caption, token):
    me = ig_get("me", fields="user_id,username", access_token=token)[1]
    uid = me.get("user_id") or me.get("id")
    if not uid:
        raise RuntimeError("Instagram user_id が取れません: {}".format(me))
    urls = ["{}/images/{}.jpg".format(IMAGE_REPO_RAW, it["id"]) for it in items]
    if len(items) == 1:
        c = ig_post("{}/media".format(uid), image_url=urls[0], caption=caption, access_token=token)
    else:
        children = []
        for u in urls:
            c = ig_post("{}/media".format(uid), image_url=u, is_carousel_item="true", access_token=token)
            children.append(c["id"])
            time.sleep(2)
        c = ig_post("{}/media".format(uid), media_type="CAROUSEL", children=",".join(children),
                    caption=caption, access_token=token)
    if not wait_container(c["id"], token):
        raise RuntimeError("container not ready: {}".format(c))
    r = ig_post("{}/media_publish".format(uid), creation_id=c["id"], access_token=token)
    return r.get("id")


# ---------- main ----------
def main():
    dry = "--dry-run" in sys.argv
    posted = json.loads(POSTED.read_text(encoding="utf-8")) if POSTED.exists() else {}
    listings = fetch_listings()
    unposted = [it for it in listings if it["id"] not in posted]
    unposted.sort(key=lambda x: x["created"], reverse=True)
    new = unposted[:MAX_ITEMS]
    print("出品 {} 件 / 未投稿 {} 件 → 今回 {} 件".format(len(listings), len(unposted), len(new)))
    if not new:
        return
    for it in new:
        make_image(it)
        print("  ", it["id"], "${:,.0f}".format(it["price"]), it["title"][:60])
    caption = caption_for(new)
    (BASE / "last_caption.txt").write_text(caption, encoding="utf-8")
    if dry:
        print("\n--- caption ---\n" + caption)
        return
    if not IMAGE_REPO_RAW:
        raise SystemExit("IMAGE_REPO_RAW が未設定です")
    import ig_token
    token = ig_token.get_token()
    media_id = publish(new, caption, token)
    now = datetime.now(JST).isoformat(timespec="minutes")
    for it in new:
        posted[it["id"]] = {"title": it["title"], "price": it["price"], "posted_at": now, "media_id": media_id}
    POSTED.write_text(json.dumps(posted, ensure_ascii=False, indent=2), encoding="utf-8")
    print("投稿完了 media_id={}".format(media_id))


if __name__ == "__main__":
    main()
