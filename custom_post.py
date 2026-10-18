# -*- coding: utf-8 -*-
"""手作りの画像とキャプションを1回だけ投稿する（定期投稿とは別枠）。

topic_images/ に置いた画像（1枚なら単体投稿、2枚以上ならカルーセル）と
キャプションのテキストファイルを指定して、GitHub Actions の custom.yml から実行する。
画像は Instagram が raw URL を取りに来るので、先にリポジトリへ push しておくこと。

使い方:
  python custom_post.py --images vault-to-vault-1.jpg,vault-to-vault-2.jpg --caption vault-to-vault-caption.txt
"""
import argparse
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import insta_post as ip

BASE = Path(__file__).parent
IMAGES = BASE / "topic_images"
POSTED = BASE / "custom_posted.json"
JST = timezone(timedelta(hours=9))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--images", required=True, help="topic_images/ 内のファイル名をカンマ区切り")
    a.add_argument("--caption", required=True, help="topic_images/ 内のキャプションファイル名")
    args = a.parse_args()

    names = [n.strip() for n in args.images.split(",") if n.strip()]
    for n in names:
        if not (IMAGES / n).exists():
            raise SystemExit("画像がありません: " + n)
    caption = (IMAGES / args.caption).read_text(encoding="utf-8").strip()

    repo = os.environ.get("IMAGE_REPO_RAW", "")
    if not repo:
        raise SystemExit("IMAGE_REPO_RAW が未設定です")
    urls = ["{}/topic_images/{}".format(repo, n) for n in names]

    import ig_token
    token = ig_token.get_token()
    me = ip.ig_get("me", fields="user_id,username", access_token=token)[1]
    uid = me.get("user_id") or me.get("id")
    if not uid:
        raise RuntimeError("Instagram user_id が取れません: {}".format(me))

    if len(urls) == 1:
        c = ip.ig_post("{}/media".format(uid), image_url=urls[0], caption=caption, access_token=token)
    else:
        children = []
        for u in urls:
            ch = ip.ig_post("{}/media".format(uid), image_url=u, is_carousel_item="true", access_token=token)
            if not ip.wait_container(ch["id"], token):
                raise RuntimeError("carousel item not ready: {}".format(u))
            children.append(ch["id"])
        c = ip.ig_post("{}/media".format(uid), media_type="CAROUSEL", children=",".join(children),
                       caption=caption, access_token=token)
    if not ip.wait_container(c["id"], token):
        raise RuntimeError("container not ready: {}".format(c))
    r = ip.ig_post("{}/media_publish".format(uid), creation_id=c["id"], access_token=token)

    posted = json.loads(POSTED.read_text(encoding="utf-8")) if POSTED.exists() else {}
    posted[args.caption] = {"images": names, "posted_at": datetime.now(JST).isoformat(timespec="minutes"),
                            "media_id": r.get("id")}
    POSTED.write_text(json.dumps(posted, ensure_ascii=False, indent=2), encoding="utf-8")
    print("投稿完了 media_id={}".format(r.get("id")))


if __name__ == "__main__":
    main()
