# -*- coding: utf-8 -*-
"""topics.py の相場ウォッチ用に、eBay Browse API で現在の最安を調べる小さなラッパー。

ebay-stock-monitor 側の ebay_search.py と同じことをするが、こちらは
環境変数（GitHub Secrets）だけで動くよう独立させてある。
"""
import base64
import os
import time

import requests

TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

EXCLUDE = ["sleeve", "acrylic", "fits case", "case fits", "no promo", "without promo",
           "opened", "deck box", "deck shield", "individual", "empty", "box only",
           "promo card only", "psa", "bgs", "cgc", "ars", "graded", "proxy", "custom"]

_tok = {"v": None, "exp": 0}


def _app_token():
    if _tok["v"] and time.time() < _tok["exp"]:
        return _tok["v"]
    basic = base64.b64encode("{}:{}".format(os.environ["EBAY_APP_ID"], os.environ["EBAY_CERT_ID"]).encode()).decode()
    r = requests.post(TOKEN_URL,
                      headers={"Authorization": "Basic " + basic,
                               "Content-Type": "application/x-www-form-urlencoded"},
                      data={"grant_type": "client_credentials",
                            "scope": "https://api.ebay.com/oauth/api_scope"}, timeout=30)
    r.raise_for_status()
    j = r.json()
    _tok["v"] = j["access_token"]
    _tok["exp"] = time.time() + int(j.get("expires_in", 7200)) - 120
    return _tok["v"]


def competition(query, must=(), exclude=EXCLUDE):
    h = {"Authorization": "Bearer " + _app_token(), "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"}
    r = requests.get(SEARCH_URL, headers=h, timeout=30,
                     params={"q": query, "limit": 50, "sort": "price",
                             "filter": "buyingOptions:{FIXED_PRICE}"})
    if r.status_code != 200:
        return {"total": 0, "jp_count": 0, "lowest": None, "jp_lowest": None}
    items, jp = [], []
    for it in r.json().get("itemSummaries", []):
        title = it["title"].lower()
        if any(x in title for x in exclude):
            continue
        if must and not all(m.lower() in title for m in must):
            continue
        price = float(it["price"]["value"])
        loc = (it.get("itemLocation") or {}).get("country")
        items.append(price)
        if loc == "JP":
            jp.append(price)
    return {"total": len(items), "jp_count": len(jp),
            "lowest": min(items) if items else None,
            "jp_lowest": min(jp) if jp else None}
