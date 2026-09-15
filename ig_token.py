# -*- coding: utf-8 -*-
"""Instagram 長期トークン（60日）の保管と自動更新。

- 初回: 環境変数 IG_ACCESS_TOKEN を使い、IG_TOKEN_KEY(Fernet鍵)で暗号化して ig_token.enc に保存
- 2回目以降: ig_token.enc を復号して使う。発行から24時間以上経っていれば refresh して保存し直す
  （公開リポジトリに置いても IG_TOKEN_KEY が無ければ復号できない）
"""
import json
import os
import sys
import time
from pathlib import Path

import requests
from cryptography.fernet import Fernet

ENC = Path(__file__).parent / "ig_token.enc"
REFRESH_URL = "https://graph.instagram.com/refresh_access_token"


def _fernet():
    key = os.environ.get("IG_TOKEN_KEY")
    if not key:
        raise SystemExit("IG_TOKEN_KEY が未設定です（python ig_token.py --newkey で生成）")
    return Fernet(key.encode())


def _load():
    if not ENC.exists():
        return None
    return json.loads(_fernet().decrypt(ENC.read_bytes()).decode())


def _save(token, obtained):
    ENC.write_bytes(_fernet().encrypt(json.dumps({"token": token, "obtained": obtained}).encode()))


def get_token():
    rec = _load()
    if rec is None:
        tok = os.environ.get("IG_ACCESS_TOKEN")
        if not tok:
            raise SystemExit("IG_ACCESS_TOKEN が未設定で ig_token.enc も無い")
        rec = {"token": tok, "obtained": time.time()}
        _save(rec["token"], rec["obtained"])
        print("ig_token.enc を作成")
    # 24時間以上経過していれば更新（Instagramの仕様: 発行後24h経たないと refresh 不可）
    if time.time() - rec["obtained"] > 24 * 3600:
        r = requests.get(REFRESH_URL, params={"grant_type": "ig_refresh_token", "access_token": rec["token"]}, timeout=30)
        if r.status_code == 200 and "access_token" in r.json():
            rec = {"token": r.json()["access_token"], "obtained": time.time()}
            _save(rec["token"], rec["obtained"])
            print("トークンを更新（有効期限 {} 日）".format(r.json().get("expires_in", 0) // 86400))
        else:
            print("トークン更新失敗（既存トークンで続行）:", r.status_code, r.text[:200])
    return rec["token"]


if __name__ == "__main__":
    if "--newkey" in sys.argv:
        print(Fernet.generate_key().decode())
    else:
        print("OK" if get_token() else "NG")
