# コンテンツカレンダー

方針は CLAUDE.md の「運用方針」節（目的=DM 直接取引、ターゲット=米国の高額コレクター、トーン=顔の見える日本の個人店）。

## 週の型

| 曜日（JST） | 時刻 | 米国では | 種類 | 中身 |
|---|---|---|---|---|
| 毎日 | 10:17 | 前日の夜 | 自動: 新着出品カルーセル | insta_post.py（eBay 価格つき） |
| 毎日 | 20:17 | 当日の朝 | 自動: 日本のポケカ情報 | topics.py（ニュース／Japan Market Watch） |
| **月** | **9:00** | **日曜の夜** | 手作り: **Sunday Grail** | 高額品を1枚（または1種）だけ主役にする |
| **木** | **9:00** | **水曜の夜** | 手作り: **From Japan** | 下の4種を順番に回す |

- 9:00 JST は米東部 20:00／西部 17:00（11/1 の夏時間終了後は東部 19:00／西部 16:00）。
  自動カルーセル（10:17）より先に出す。遅れても 13:00 JST までなら米国の夜に収まる

### Sunday Grail（月）

- カルーセル 3〜5 枚: スラブ表 → 裏 → PSA の cert 画像 → 解説カード（自前で描画。日本限定の理由・発行年・
  PSA の個体数など）
- キャプション: なぜ珍しいかを 2〜3 行 → "I have it in hand / in PSA Vault" → **価格は出さず DM で**
- Vault 品には「Vault to Vault で発送なし・即受け渡し」と添える

### From Japan（木）の 4 種

1. **仕入れの裏側** — 日本でカードを探す・届く・検品する様子。自分で撮った写真だけ（店内や他人の顔は写さない）
2. **Japan Exclusive 解説** — 日本でしか出ていないプロモの背景（キャンペーン・ポケモンセンター限定など）。
   最後に自分の在庫へつなげる
3. **Vault まとめ** — Vault 在庫の上位 6〜8 種を並べる（vault/mk_post.py）。先に「vault更新」をしておく
4. **直接購入の流れ** — DM で問い合わせ → 見積もり → Wise で支払い → 追跡つき発送 → 関税の扱い。
   DM へ送る一番の後押しになる投稿。**eBay の $1 商品に同梱する方法は書かない**

月に5回目の木曜があるときや季節の行事（ハロウィン、ブラックフライデー等）は差し替えてよい。

## 予定

状態: 予定 → 準備済（画像とキャプションを topic_images/ に用意しユーザー確認待ち） → 済（media_id を記入）

| 日付（JST） | 型 | 中身（候補） | 状態 |
|---|---|---|---|
| 10/19（月） | Sunday Grail | Poncho-wearing Eevee #140 エーフィ柄 PSA 9 / #141 ブラッキー柄 PSA 8（Vault）— grail-20261019-1〜4.jpg ＋ grail-20261019-caption.txt | 準備済 |
| 10/22（木） | Japan Exclusive | 7-Eleven Bento Box Pikachu PSA 7（2015 セブンイレブン弁当、Vault） | 予定 |
| 10/26（月） | Sunday Grail | Mega Gengar ex SAR PSA 10（M2a、Vault）— ハロウィンの週 | 予定 |
| 10/29（木） | 直接購入の流れ | DM → 見積もり → Wise → 追跡つき発送 → 関税 | 予定 |
| 11/2（月） | Sunday Grail | Mega Charizard X ex SAR PSA 10 ×4（M2、Vault）— 夏時間終了後の初回 | 予定 |
| 11/5（木） | 仕入れの裏側 | 撮影が必要（ユーザーに依頼） | 予定 |
| 11/9（月） | Sunday Grail | Lugia V Full Art PSA 10（Paradigm Trigger、Vault） | 予定 |
| 11/12（木） | Vault まとめ | 上位 8 種（事前に vault更新） | 予定 |
| 11/16（月） | Sunday Grail | PSA 10 連番 Pikachu / Pichu（Mysterious Mountains、eBay 出品中） | 予定 |
| 11/19（木） | Japan Exclusive | ポケモンセンター限定プロモ（Yokohama's Pikachu ほか） | 予定 |
| 11/23（月） | Sunday Grail | Charizard 25th Anniversary PSA 10 / Charizard ex SAR PSA 10（151） | 予定 |
| 11/26（木） | 季節（差し替え） | ブラックフライデー（米国 11/27）の DM 限定価格の告知 — **値引き内容はユーザーが決める** | 予定 |

## 回し方

- Sunday Grail の画像は `python grail_post.py <日付>`（`GRAILS` に日付ごとの中身を足す。スラブ写真は PSA の
  cert 画像を `vault/vault_dump.txt` のパスの thumbnail→large で取得）
- 手作り投稿は **前日までに** Claude が画像（1080×1350、CLAUDE.md の「デザインの決まり」どおり）と
  キャプション（英語＋日本語訳）を `topic_images/` に用意し、状態を「準備済」にする
- ユーザーが確認して「投稿して」と言ったら、custom.yml（instagram-custom-post）を起動する
- 投稿後は状態を「済」にし、media_id を書く
- 毎月の最後の週に翌月分の予定を書き足す。候補は Vault 在庫（vault/vault_dump.txt の推定額上位）と
  eBay の高額出品から選ぶ
