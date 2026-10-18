# -*- coding: utf-8 -*-
"""vault_dump.txt（PSA Vault の一覧）→ グループ化した data.json（画像は data URI で埋め込み）"""
import base64
import json
import re
import sys
import urllib.request
from pathlib import Path

import truststore
truststore.inject_into_ssl()

HERE = Path(__file__).parent
CDN = "https://d1htnxwo4o0jhw.cloudfront.net/cert/"
LINE = re.compile(r"^(#\S+) (.+?) ((?:19|20)\d\d .+) (PSA \d+) (\d{6,}) (\$[\d,.]+) (.+) (\S+\.jpg)$")
KEEP_UPPER = {"GX", "V", "VMAX", "VSTAR", "SAR", "AR", "SR", "UR", "HR", "BW", "SV", "SM", "XY", "ST", "PSA",
              "M-P", "SV-P", "S", "US"}


def tidy_word(w):
    if w in ("|", "&", "ex", "/"):
        return w
    if re.fullmatch(r"\d+(ST|ND|RD|TH)", w):
        return w.lower()
    if "-" in w and any(c.isdigit() for c in w):
        return "-".join(tidy_word(p) for p in w.split("-"))
    if any(c.isdigit() for c in w):
        return w
    if w.upper() in KEEP_UPPER:
        return w.upper()
    if w.upper() == "MCDONALD'S":
        return "McDonald's"
    t = w.lower().capitalize()
    t = re.sub(r"(?<=[-/])([a-z])", lambda m: m.group(1).upper(), t)
    return t


def tidy(s):
    s = " ".join(tidy_word(w) for w in s.split(" ") if w)
    s = re.sub(r"(Ex|EX)", "ex", s)
    return s


def tidy_name(n):
    n = tidy(n).replace("-Holo", " Holo")
    if n.startswith("Full Art/"):
        n = n[len("Full Art/"):] + " (Full Art)"
    return n


def tidy_set(setline):
    s = re.sub(r"^(19|20)\d\d ", "", setline)
    s = re.sub(r"^(POKEMON|ONE PIECE|YU-GI-OH!) (JAPANESE )?", "", s)
    s = tidy(s).replace(" | ", " · ")
    s = re.sub(r"(?<=[A-Za-z0-9])-(?=[A-Z][a-z])", " ", s)
    s = s.replace("Starter Deck ex", "Starter Deck EX")
    return s


def game(setline):
    s = setline.upper()
    if "ONE PIECE" in s:
        return "One Piece"
    if "YU-GI-OH" in s:
        return "Yu-Gi-Oh!"
    return "Pokémon"


rows = []
for ln in (HERE / "vault_dump.txt").read_text(encoding="utf-8").splitlines():
    m = LINE.match(ln.strip())
    if not m:
        print("skip:", ln[:60], file=sys.stderr)
        continue
    num, name, setline, grade, cert, est, tags, img = m.groups()
    if "AWAITING PAYMENT" in tags:   # 売却済み・支払い待ち
        continue
    rows.append(dict(num=num, name=name, set=setline, grade=grade, cert=cert,
                     est=float(est.replace("$", "").replace(",", "")), img=img))

groups = {}
for r in rows:
    k = (r["num"], r["name"], r["set"], r["grade"])
    g = groups.setdefault(k, dict(num=r["num"].lstrip("#"), name=tidy_name(r["name"]), set=tidy_set(r["set"]),
                                 year=r["set"][:4], game=game(r["set"]), grade=int(r["grade"].split()[1]),
                                 est=r["est"], certs=[], img=r["img"]))
    g["certs"].append(r["cert"])

items = sorted(groups.values(), key=lambda g: (-g["est"], -g["grade"]))
for g in items:
    url = CDN + g["img"]
    data = urllib.request.urlopen(url, timeout=30).read()
    g["img"] = "data:image/jpeg;base64," + base64.b64encode(data).decode()
    g["certs"].sort()
    del g["est"]
(HERE / "data.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
print("rows", len(rows), "groups", len(items), "bytes", (HERE / "data.json").stat().st_size)
for g in items[:8]:
    print(g["grade"], g["name"], "|", g["set"], "| x", len(g["certs"]))
