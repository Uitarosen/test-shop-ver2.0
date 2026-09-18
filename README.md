# AUGUST SHOP — 公式サイト ver2.0（静的サイト）

`august-shop-renewal-mock_20260918.zip`（マルチページ版デザインモック）のアセットをもとに構築した、
そのまま公開できる静的サイトです。ビルドツールは不要で、このフォルダの中身をサーバーへ
アップロードすればそのまま動作します。

## 1. 構成

```
shopsite ver2.0/
├── index.html          トップページ
├── buy.html            買取について（対面／宅配・フォーム／宅配・LINE／FAQ）
├── form.html           買取フォーム
├── about.html          店舗紹介・会社概要
├── shop.html           販売について（営業日・アクセス・決済方法）
├── restore.html        リペア・お直し（Coming Soon）
├── instagram.html      インスタグラム（Coming Soon）
├── privacy.html        プライバシーポリシー
├── 404.html            エラーページ（noindex）
├── robots.txt / sitemap.xml / .nojekyll
├── NOTICE-fonts.txt    同梱フォントの出典とライセンス
├── tools/
│   └── sync-common.py  共通パーツ・メタ情報の同期スクリプト（公開ファイルではありません）
└── assets/
    ├── css/style.css   デザイン本体（全ページ共通）
    ├── css/fonts.css   同梱Webフォントの @font-face 定義
    ├── js/main.js      スクロール演出・ドロワー・タブ・アコーディオン・フォーム送信
    ├── img/            写真素材（すべてプレースホルダー）＋ og.jpg（OGP用）
    ├── icon/           favicon / apple-touch-icon / LINE QR / ロゴ
    └── fonts/          Webフォント（woff2）＋ licenses/
```

## 2. ローカル確認

```bash
python3 -m http.server 4174
```

→ http://localhost:4174

## 3. モック版からの変更点

### 構造

- **共通パーツをHTMLに直接出力**（モックでは `assets/js/layout.js` がJavaScriptで生成していました）。
  JavaScriptが無効でもヘッダー・フッターが表示され、検索エンジンにも確実に読まれます。
  かわりに、共通部分は `tools/sync-common.py` で一括更新できるようにしています（→ 4章）。
- `privacy.html` / `404.html` / `robots.txt` / `sitemap.xml` を追加。
- 買取フォームを**実際に送信できる作り**に変更（→ 5章）。

### SEO / SNS

- 全ページの `<head>` を刷新：canonical / OGP / Twitter Card / favicon。
- 構造化データ（schema.org）：トップに `Store`（住所・電話・営業時間つき）、
  下層ページに `BreadcrumbList`、`buy.html` に `FAQPage`。
- OGP画像 `assets/img/og.jpg`（1200×630）を追加。
- `sitemap.xml` は `tools/sync-common.py` が自動生成します。

### 表示・パフォーマンス

- 画像を再圧縮（4.4MB → 1.4MB）。すべての `<img>` に `width` / `height` / `loading` / `decoding` を付与し、
  レイアウトのガタつき（CLS）を防止。ヒーロー画像のみ `fetchpriority="high"` で先読み。
- 地図のプレースホルダーを **Google マップの埋め込み**に差し替え（`index.html` / `shop.html`）。
- LINE査定セクションのQRコードを実画像（`assets/icon/line-qr.png`）に差し替え。

### アクセシビリティ / 堅牢性

- スキップリンク、`:focus-visible` のアウトラインを追加。
- ドロワーメニューにフォーカストラップとフォーカス復帰（Escapeで閉じる）を実装。
- JavaScript無効時のフォールバック（`html.no-js`）：タブ・アコーディオンの中身をすべて展開表示。
- **不具合修正**：`hidden` 属性がCSSで打ち消され、買取フォームの完了メッセージが
  常時表示されていた問題を修正（`[hidden]{display:none!important}`）。

### リンク

- LINE友だち追加：`https://line.me/R/ti/p/%40776yyqfq`
- Instagram：`https://www.instagram.com/august_shop/`（フッター・instagram.html）
- 各モール（ヤフオク!・楽天市場・メルカリ・BASE）は URL 未確定のため、
  リンク切れを避けて「準備中」表示にしています（→ 6章）。

## 4. 共通パーツ・サイト情報の変更方法

ヘッダー・キャンペーンバー・ドロワー・LINE査定セクション・フッター・追従CTA、
および各ページの `<head>` は、`tools/sync-common.py` が管理しています。

各HTMLの下記マーカーで囲まれた範囲が、スクリプトの出力で置き換わります。
マーカーの外側（`<main>` の中身）はページ固有の内容なので、直接編集して問題ありません。

```html
<!-- @common:head -->   … <head> 全体
<!-- @common:chrome --> … スキップリンク／キャンペーンバー／ヘッダー／ドロワー
<!-- @common:foot -->   … LINE査定セクション／フッター／追従CTA／<script>
```

電話番号・メニュー項目・キャンペーンバーの文言・各ページのタイトルやディスクリプションは、
スクリプト冒頭の `SITE` と `PAGES` を書き換えて実行してください。

```bash
python3 tools/sync-common.py          # 全ページへ反映し sitemap.xml / robots.txt を再生成
python3 tools/sync-common.py --check  # 差分の有無だけ確認（書き換えない）
```

### 確認用URLと本番URLの切り替え（重要）

スクリプト冒頭の `PREVIEW` で、公開先に応じた設定を切り替えます。

| | `PREVIEW = True`（現在） | `PREVIEW = False`（本番公開時） |
| --- | --- | --- |
| 基準URL | `PREVIEW_ORIGIN`（GitHub Pages） | `SITE["origin"]`（august-shop.net） |
| meta robots | `noindex, nofollow` を出力 | canonical を出力 |
| robots.txt | `Disallow: /`（クロール禁止） | `Allow: /` ＋ sitemap の記載 |

**現在は確認用URLでの公開のため `PREVIEW = True`**（検索結果に出ません）。
6章のTODOを差し替えて本番ドメインへ移す際に、`PREVIEW = False` にして
`python3 tools/sync-common.py` を実行してください。

> [!NOTE]
> `tools/` はサーバーへアップロードする必要はありません。
> WordPress等へ移植する際は、`sync-common.py` の `build_chrome` / `build_foot` の出力を
> header.php / footer.php に置き換える想定です。

### 配色・フォント

`assets/css/style.css` 冒頭の `:root` にすべて定義しています。

| 変数 | 値 | 用途 |
| --- | --- | --- |
| `--ink` | `#14150f` | 文字・基調色 |
| `--bg-alt` | `#f6f4ef` | セクション背景（アイボリー） |
| `--bg-dark` | `#16170f` | 反転セクション |
| `--accent` | `#1f6f66` | アクセント（リンク・強調） |
| `--alert` | `#b8452f` | 注意・定休日 |
| `--line-green` | `#06c755` | LINEボタン |

Jost / Shippori Mincho / Zen Kaku Gothic New の3書体を `assets/fonts/` に同梱しています
（すべて SIL Open Font License 1.1。詳細は `NOTICE-fonts.txt`）。
CDN配信に戻す場合は、`tools/sync-common.py` の `build_head` にある
`assets/css/fonts.css` の行を Google Fonts の `<link>` に差し替えてください。

## 5. 買取フォームについて

`form.html` の `<form id="buyform" data-endpoint="">` に送信先URLを設定すると、
`assets/js/main.js` が `FormData`（画像添付を含む）を POST します。

```html
<form id="buyform" data-endpoint="https://formspree.io/f/xxxxxxxx" method="post" enctype="multipart/form-data" novalidate>
```

- 送信成功 → 完了メッセージ（`#formdone`）を表示し、フォームをリセットします。
- 送信失敗 → 再試行と買取専用メールの案内を表示します。
- **`data-endpoint` が空のあいだは送信されません。**
  この場合、「送信できた」と誤解させないよう、LINE・メールでの連絡を促すメッセージを表示します。

Formspree / Google Apps Script など、`multipart/form-data` を受け取れるサービスをご利用ください。
自社サーバーで受ける場合は、CSRF対策・添付ファイルのサイズ／拡張子チェック・送信元の
レート制限をあわせてご検討ください。

## 6. 公開前に差し替えが必要な項目（TODO）

該当箇所には HTML 内にも `<!-- TODO(公開前): ... -->` のコメントを入れています。

| 優先度 | 項目 | 現在の内容 | 場所 |
| --- | --- | --- | --- |
| **必須** | **買取実績の金額** | **サンプル値（実在の取引ではありません）** | `buy.html` の `#results` |
| **必須** | **キャンペーン・クーポン** | **サンプル3件（AUG15 / STORE5 / FIRST10）** | `index.html` の `#campaign`、`tools/sync-common.py` の `topbar_text` |
| **必須** | 買取フォームの送信先 | 未接続（`data-endpoint=""`） | `form.html` |
| **必須** | プライバシーポリシーの制定日・最終改定日 | `[　YYYY年M月D日　]` | `privacy.html` 末尾 |
| 高 | 写真 | 生成画像のプレースホルダー | `assets/img/` |
| 高 | LINEのQRコード | ver1.0 から流用。読み取り先が `@776yyqfq` であることをご確認ください | `assets/icon/line-qr.png` |
| 高 | 決済方法の対応ブランド | サンプル | `shop.html` の `#payment` |
| 中 | アクセス（最寄駅からの所要時間・バス経路・駐車場） | 未記載 | `shop.html` の `#access` |
| 中 | ブランドリンク（ヤフオク!・楽天市場・メルカリ・BASE） | 「準備中」表示 | `shop.html` の `#online` |
| 中 | 買取専用メールアドレス | `kaitori@august-shop.net`（提案） | `tools/sync-common.py` の `SITE.mail` |
| 低 | 本番ドメイン | `https://august-shop.net` | `tools/sync-common.py` の `SITE.origin`、`robots.txt` |
| 低 | アクセス解析を導入する場合の記載 | 未記載 | `privacy.html` の8章 |

> [!WARNING]
> 買取実績の金額とキャンペーン内容はモック由来のサンプルです。
> 実際の内容に差し替えずに公開すると、景品表示法上の問題となるおそれがあります。

**法令面の注意**：古物営業法により、古物商はウェブサイト上に許可を受けた公安委員会名・許可番号・
氏名（名称）の表示が必要です。本サイトではフッター、`about.html#company`、`privacy.html` に
掲載しています（古物商許可証 第452740013242号／神奈川県公安委員会）。
自社サイト上で商品を販売する場合は、別途「特定商取引法に基づく表記」ページが必要になります。

## 7. デプロイ

### 現在の確認用URL（GitHub Pages）

https://uitarosen.github.io/test-shop-ver2.0/

`main` ブランチのルートを GitHub Pages が配信しています。
`git push` するだけで反映されます（反映まで1〜2分）。
確認用のため `noindex` ＋ `robots.txt` でクロールを禁止しています（→ 4章）。

### 本番公開

静的ホスティング（Netlify / Vercel / Cloudflare Pages / S3 / レンタルサーバー等）に
そのまま配置できます。`tools/` は不要です。
公開前に `tools/sync-common.py` の `PREVIEW` を `False` にして実行してください。

404ページを有効にするには、ホスティング側で404時の表示先を `/404.html` に設定してください。
（Netlify / Cloudflare Pages はルート直下の `404.html` を自動で使用します。Apache の場合は
`.htaccess` に `ErrorDocument 404 /404.html` を追記してください。）

## 8. 動作環境

- モダンブラウザ全般（Chrome / Safari / Firefox / Edge の最新版）
- レスポンシブ対応（ブレークポイント: 1100px / 900px / 640px）
- `prefers-reduced-motion` 対応（アニメーション無効設定を尊重）
- JavaScript無効時も、全ページの内容を閲覧できます。
  画面幅1100px以下ではドロワーメニューが使えなくなりますが（ハンバーガーボタンは非表示になります）、
  フッターのナビゲーションから全ページへ移動できます
