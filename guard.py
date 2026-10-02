# -*- coding: utf-8 -*-
"""今日の投稿が済んでいれば skip=true を GITHUB_OUTPUT に書く（二重投稿防止）。

cron-job.org（本命）と GitHub schedule（予備）の両方から起動されるため、
先に動いた方だけが投稿し、後から来た方は何もしない。

  python guard.py post    商品投稿（posted.json）。JSTの暦日で判定
  python guard.py topic   トピック投稿（topics_posted.json）。20時予定が日付をまたいで
                          遅れても同じ日として扱うため、JST-6時間の日付で判定
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))
BASE = Path(__file__).parent
CONF = {"post": ("posted.json", 0), "topic": ("topics_posted.json", 6)}


def logical_day(dt, shift_h):
    return (dt.astimezone(JST) - timedelta(hours=shift_h)).date()


def main():
    kind = sys.argv[1]
    fname, shift = CONF[kind]
    path = BASE / fname
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    today = logical_day(datetime.now(JST), shift)
    done = any(
        logical_day(datetime.fromisoformat(v["posted_at"]), shift) == today
        for v in data.values() if isinstance(v, dict) and v.get("posted_at"))
    print("{}: 今日({}) 投稿済み={}".format(kind, today, done))
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write("skip={}\n".format("true" if done else "false"))


if __name__ == "__main__":
    main()
