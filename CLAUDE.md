# CLAUDE.md — fancy-tcg-ig（Instagram 運用）

Instagram アカウント **@fancy_tcg_japan** の運用リポジトリ。日本のポケカ（一部ワンピース）を
海外コレクター向けに英語で発信し、eBay の出品と直接取引（DM）に送客する。
2026-10-18 に eBay 側のセッション（`claude関連\ebay-stock-monitor`）から切り出した。
eBay の出品・監視・利益計算はあちらのリポジトリと CLAUDE.md を参照。

## アカウントと事業の前提

- 運営者は日本の個人事業（eBay セラー `fancy_tcg_japan`）。仕入れは主にメルカリ（無在庫販売）、
  一部は手持ち在庫と PSA Vault 内の鑑定品
- プロフィールの自己紹介（2026-10 時点・140/150字）:
  JP Pokémon cards direct from Japan / Skip the eBay fees — DM me for a lower price /
  Quotes, requests, bundles all welcome | Worldwide
- プロフィールのリンク: eBay ストア（ebay.io/m/DCbUEO）＋ PSA Vault 在庫ページ（下記）。
  リンク編集はスマホアプリのみ（PC ブラウザ版では不可）
- 対象は海外コレクター。**投稿・キャプションは英語**。日本語は確認用に添えるだけ

## 投稿の種類と仕組み

| 種類 | スクリプト | ワークフロー | 時刻（JST） | 二重投稿防止 |
|---|---|---|---|---|
| 新着出品カルーセル | insta_post.py | post.yml | 10:17 | posted.json（guard.py post） |
| 日本のポケカ情報（ニュース／相場） | topics.py | topics.yml | 20:17 | topics_posted.json（guard.py topic） |
| 手作り投稿（1回だけ） | custom_post.py | custom.yml（手動のみ） | 任意 | custom_posted.json |

- 本命の起動は **cron-job.org から workflow_dispatch**。GitHub の `schedule:` は混雑で4〜7時間
  遅れるので予備扱い（2026-10-02 実測）。両方動いても guard.py が後発を止める
- 画像は Instagram が **GitHub の raw URL を取りに来る**。投稿前に画像を commit & push しておくこと
  （`IMAGE_REPO_RAW=https://raw.githubusercontent.com/fancymakemego/fancy-tcg-ig/main`）
- 新着出品: eBay Browse API で自分の出品を取得 → 未投稿の新しい順に最大10件 → 4:5（1080×1350）に
  白背景パディング（Instagram API は 4:5〜1.91:1 以外を拒否する）
- 情報投稿: `topics.json` の未投稿エントリ（ニュース優先、英文は事前に用意）→ 無ければ
  「Japan Market Watch」を eBay の日本セラー最安から自動生成。`python topics.py --news` で公式の新着を表示
  （topics.json 補充用・投稿はしない）

### 手作り投稿（custom_post.py）の手順

1. 画像（1080×1350 推奨）とキャプションの txt を `topic_images/` に置く
2. commit & push（raw URL が 200 を返すことを確認）
3. Actions の **instagram-custom-post** を workflow_dispatch で起動
   - inputs: `images`（カンマ区切り。2枚以上でカルーセル）、`caption`（txt のファイル名）
   - ローカルからは GitHub API の dispatches を叩く（`gh` は未導入）。認証は `git credential fill` の
     トークンをプロセス内だけで使い、**表示・ログ出力しない**
4. 結果は custom_posted.json（media_id）に残る

**投稿は公開行為なので、ユーザーが「投稿して」と明示したときだけ実行する。**

## デザインの決まり

- 1080×1350、背景 (18,20,28)、文字 (245,246,250)、アクセント黄 (255,203,5)、補助 (150,157,175)
- 上下に黄色の帯（14px）、左下に `@fancy_tcg_japan` ＋ "Japanese cards, shipped from Japan"
- フォントは Linux=DejaVu、Windows=Segoe UI（`topics.py` の `_font`）
- **画像に絵文字を入れない**（フォントに無く豆腐になる）。絵文字はキャプション側で使う
- **他人の写真・公式画像は使わない**（権利問題）。使ってよいのは自前の描画、自分の出品写真、
  自分の PSA スラブの写真（PSA の cert 画像）
- ハッシュタグは各スクリプトの `HASHTAGS` 定数。15個前後

## PSA Vault 在庫ページ（vault/）

PSA の Vault to Vault（2026-10 開始）で、Vault 内の鑑定品を発送なしで売れる。その在庫一覧ページ。

- 公開URL: https://claude.ai/artifact/JvpTtbeBCP2V4vbj5fj89s （「リンクを知っている全員」で共有済み）
- 価格は載せない（"Prices on request"・DM 誘導）。cert 番号は PSA の公開 cert ページにリンク
- 2026-10-18 時点: 118枚 / 33種類

### 更新手順（「vault更新して」と言われたら）

1. ユーザーの Chrome（PSA にログイン済み）で psacard.com/myaccount →「Collection & Vault」→
   **Vault タブ** → フィルタ「Vaulted」にチェック。1ページ50件なので全ページを回る
2. 各ページで行（`tr`）から 番号+名前 / セット / グレード / cert / 推定額 / タグ / サムネイルを抜く。
   **サムネイルは遅延読み込み**で、下の行ほど `data:image/svg+xml` のダミーになる。
   新規の cert だけ実画像URLを確保し、既存分は `vault_dump.txt` の行を流用するのが確実
3. `vault/vault_dump.txt` を1行1枚で更新（形式は既存行と同じ。`AWAITING PAYMENT` は自動で除外される）
4. `cd vault && python build_data.py && python fix_names.py && python build_html.py`
5. `fancy-tcg-vault.html` を **Artifact の url 指定で同じURLに再公開**（別セッションからは url を渡さないと
   新しいURLになる。publish の前に read が必要）
6. 同じ URL のままなのでインスタのリンクは貼り直し不要

告知画像は `vault/mk_post.py`（cwd=vault、data.json から上位8種のスラブ写真を並べる）。
2026-10-18 に告知投稿済み（vault-to-vault-1/2.jpg、プロフィールに固定）。

## DM・直接取引のルール（ユーザー指示）

- eBay のメッセージからインスタに誘うときは、次の言い回しを下敷きにする。
  **「Instagram」「@」「directly / outside eBay」は書かず、伏字「I  G」とアカウント名の括弧書き**にする
  （eBay は外部連絡先を検知すると送信をブロック・伏字化する）

  > I may be able to offer it for $1650 including shipping fee through a slightly different option, which would help reduce some fees on both.
  > If you're interested, it might be easier to continue this conversation somewhere I can share more details.
  > You can find me on I  G with the same icon:（fancy_tcg_japan）

- 直接取引の受け取りは **Wise**（手数料約1%）。eBay の $1 商品を買ってもらい、その注文に同梱して発送・追跡を載せる
- 米国向けは原則、関税分（価格帯上限×18%）も Wise で前払い。DHL 自社契約で DAP（関税は受取人払い）に
  することもある（CPaSS 経由でなければ可。$2,500 超は米国の Formal Entry になる）
- 規約上のリスクは一度説明済み。**毎回繰り返さない**
- 返信文は「英語（送信用）＋日本語訳（確認用）」で作る。フレンドリーなトーン、発送期限の話は書かない

## 運用の約束

- 投稿・DM送信・プロフィール変更などの公開/外部向け操作は、ユーザーの明示的な指示があるときだけ
- このリポジトリは **公開**。トークンは `ig_token.enc`（Fernet 暗号化、鍵は Secrets の IG_TOKEN_KEY）。
  平文トークン・鍵をコミット/チャット/ログに出さない
- Secrets: IG_ACCESS_TOKEN / IG_TOKEN_KEY / EBAY_APP_ID / EBAY_CERT_ID
- Python は `import truststore; truststore.inject_into_ssl()` を最初に（このPCは certifi だと SSL エラー）

## これから（2026-10-18 時点の構想）

ユーザーは「会社としてインスタ運営に力を入れ、より組織的に動きたい」。候補:
1. 投稿方針（目的・ターゲット・頻度・トーン）をユーザーと決めてこのファイルに追記
2. コンテンツカレンダー（曜日ごとの型。例: 相場 / 在庫紹介 / Vault / ニュース）をファイルで管理
3. Instagram Insights API でリーチ・保存・プロフィール訪問を週次集計
4. eBay 販売集計シート（Google Sheets `1rtymp4dnD33ULLlQ59nIytBDHHKF1nInCzOyyhHEPUw`）に「流入元：インスタ」を足し、売上貢献を見る
