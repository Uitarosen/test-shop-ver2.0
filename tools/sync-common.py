#!/usr/bin/env python3
"""AUGUST SHOP — 共通パーツ／メタ情報の同期スクリプト

各HTMLの下記マーカーで囲まれた範囲を、このファイルの定義から再生成します。

    <!-- @common:head -->   ... </head> までの <head> 全体
    <!-- @common:chrome --> ... スキップリンク／キャンペーンバー／ヘッダー／ドロワー
    <!-- @common:foot -->   ... LINE査定セクション／フッター／追従CTA／<script>

マーカーの外側（<main> の中身）はページごとの内容なので、このスクリプトは触りません。
電話番号・メニュー・OGP などを変更したいときは、このファイルの SITE / PAGES を
書き換えて実行してください。

    python3 tools/sync-common.py          # 全ページを同期し sitemap.xml を再生成
    python3 tools/sync-common.py --check  # 差分があるかだけ確認（書き換えない）
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# =========================================================
# 公開先の設定
#
# PREVIEW = True  … GitHub Pages などの確認用URLで公開する状態。
#                   全ページに noindex を出し、robots.txt でクロールを禁止します。
#                   （サンプルのままの買取実績・キャンペーンが検索結果に出るのを防ぐため）
# PREVIEW = False … 本番ドメイン（SITE["origin"]）で公開する状態。
#                   canonical を出し、robots.txt でクロールを許可します。
#
# 本番公開時は PREVIEW を False にして `python3 tools/sync-common.py` を実行してください。
# =========================================================
PREVIEW = True
PREVIEW_ORIGIN = "https://uitarosen.github.io/test-shop-ver2.0"

# =========================================================
# サイト共通の設定（ここだけ直せば全ページに反映されます）
# =========================================================
SITE = {
    "name": "August Shop",
    "name_en": "August Shop",
    "origin": "https://august-shop.net",
    "tel": "046-259-6189",
    "tel_link": "tel:046-259-6189",
    "line_id": "@776yyqfq",
    "line_url": "https://line.me/R/ti/p/%40776yyqfq",
    "instagram_url": "https://www.instagram.com/august_shop/",
    "mail": "kaitori@august-shop.net",
    "mail_info": "info@august-shop.net",
    "zip": "243-0032",
    "address": "〒243-0032　神奈川県厚木市恩名1-20-27　プチヒルズ4F",
    "address_street": "恩名1-20-27 プチヒルズ4F",
    "address_city": "厚木市",
    "address_region": "神奈川県",
    "hours": "13:00〜19:00",
    "closed": "水曜・木曜",
    "company": "株式会社SGN（SGN Co.,Ltd.）",
    "company_en": "SGN Co.,Ltd.",
    "license": "古物商許可証　第452740013242号／神奈川県公安委員会",
    # トップのキャンペーンバー（不要なら topbar_text を空文字にすると非表示）
    "topbar_tag": "CAMPAIGN",
    "topbar_text": "＼ ただいま 買取金額 <b>15%UP</b> クーポン配布中 ／ 宅配買取・LINE査定が対象です",
    "topbar_href": "index.html#campaign",
    "nav": [
        {"href": "buy.html", "en": "Buy", "jp": "買取について"},
        {"href": "form.html", "en": "Form", "jp": "買取フォーム"},
        {"href": "about.html", "en": "About", "jp": "店舗紹介"},
        {"href": "shop.html", "en": "Shop", "jp": "販売について"},
        {"href": "restore.html", "en": "Restore", "jp": "リペア・お直し"},
        {"href": "instagram.html", "en": "Instagram", "jp": "インスタグラム"},
    ],
}

def base_origin() -> str:
    """URLの組み立てに使うオリジン（プレビュー中は確認用URL）。"""
    return PREVIEW_ORIGIN if PREVIEW else SITE["origin"]


OG_IMAGE = "assets/img/og.jpg"
OG_IMAGE_W, OG_IMAGE_H = 1200, 630

# =========================================================
# ページ定義
#   title / desc  : <title> と meta description
#   crumb         : パンくず（None ならトップページ扱い）
#   line          : 共通のLINE査定セクションを出すか
#   index         : 検索エンジンに登録するか（sitemap にも連動）
# =========================================================
PAGES = {
    "index.html": {
        "title": "August Shop｜アメカジ・ブランド古着・ヴィンテージの買取と販売",
        "desc": "厚木市のアメカジ・ブランド古着専門店 August Shop。アーカイブ品から本格ヴィンテージまで、"
                "経験と知識のあるスタッフが一点一点丁寧に査定します。対面買取・宅配買取・LINE査定に対応。",
        "crumb": None,
        "priority": "1.0",
        "changefreq": "weekly",
    },
    "buy.html": {
        "title": "買取について｜August Shop",
        "desc": "August Shop の買取について。対面買取・宅配買取・LINE査定の3つの方法、査定の流れ、"
                "買取できないもの、買取実績、取り扱いブランドをご案内します。",
        "crumb": "買取について",
        "priority": "0.9",
        "changefreq": "monthly",
        "faq": [
            ("何点から買取をお願いできますか？",
             "1点からお受けしています。点数が多い場合は無料の配送キットをお送りしますので、フォームまたはLINEでお知らせください。"),
            ("査定金額の有効期限はありますか？",
             "お伝えした査定金額の有効期限は1週間です。対面買取・宅配買取・LINE査定のいずれにも適用されます。"),
            ("タグや付属品がなくても買取できますか？",
             "可能です。付属品が揃っている方が査定額は上がりますが、本体のみでもお値段をお付けできるケースが多くあります。"),
            ("キズや汚れがあるものはどうなりますか？",
             "状態がわかる写真を添えてお送りください。ヴィンテージや雰囲気として捉えられるものは、そのまま評価いたします。"
             "著しい状態不良の場合は買取をお断りすることがございます。"),
            ("査定額に納得できなかった場合は？",
             "キャンセル料は一切いただきません。送料当店負担で、お預かりしたアイテムをそのままご返送いたします。"),
            ("入金までどのくらいかかりますか？",
             "買取成立後、3営業日以内にご指定の口座へお振込いたします。なお、ご依頼者さまと名義の異なる口座へのお振込はできません。"),
        ],
    },
    "form.html": {
        "title": "買取フォーム｜August Shop",
        "desc": "August Shop の買取フォーム。お見積り・配送キットはすべて無料。このページだけでお申し込みが完結します。"
                "買取専用メール kaitori@august-shop.net",
        "crumb": "買取フォーム",
        "priority": "0.9",
        "changefreq": "yearly",
    },
    "about.html": {
        "title": "店舗紹介・会社概要｜August Shop",
        "desc": "August Shop の店舗紹介。アメカジやブランド古着を中心に、アーカイブ品から本格ヴィンテージまで。"
                "オリジナルのシルバーアクセサリーやベルトもご用意しております。会社概要・古物商許可番号も掲載。",
        "crumb": "店舗紹介",
        "priority": "0.7",
        "changefreq": "yearly",
    },
    "shop.html": {
        "title": "販売について（営業日・アクセス・決済方法）｜August Shop",
        "desc": "August Shop の販売について。営業時間13:00〜19:00、定休日は水曜・木曜。"
                "アクセス、決済方法、オンラインでの販売チャネルをご案内します。",
        "crumb": "販売について",
        "priority": "0.8",
        "changefreq": "monthly",
    },
    "restore.html": {
        "title": "リペア・お直し｜August Shop",
        "desc": "August Shop のリペア・お直し。スタッフ高瀬によるリペア、裾上げを承ります（作業金額応相談）。"
                "ご相談は店頭・お電話・LINEにて受付中です。",
        "crumb": "リペア・お直し",
        "priority": "0.5",
        "changefreq": "yearly",
    },
    "instagram.html": {
        "title": "インスタグラム｜August Shop",
        "desc": "August Shop の Instagram。新着・入荷情報、スタッフのスタイリング、臨時休業のお知らせを発信しています。",
        "crumb": "インスタグラム",
        "priority": "0.5",
        "changefreq": "yearly",
    },
    "privacy.html": {
        "title": "プライバシーポリシー｜August Shop",
        "desc": "August Shop（運営：株式会社SGN）における個人情報の取り扱い、古物営業法に基づく本人確認、"
                "開示・訂正等のご請求方法についてご案内します。",
        "crumb": "プライバシーポリシー",
        "line": False,
        "priority": "0.3",
        "changefreq": "yearly",
    },
    "404.html": {
        "title": "ページが見つかりません｜August Shop",
        "desc": "お探しのページは見つかりませんでした。",
        "crumb": "ページが見つかりません",
        "line": False,
        "index": False,
    },
}

# =========================================================
# アイコン
# =========================================================
ICON_LINE = (
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2C6.5 2 2 5.66 2 10.16c0 4.03 '
    '3.57 7.4 8.39 8.04.33.07.77.22.89.5.1.26.07.66.03.92l-.14.86c-.04.26-.2 1.02.89.56 1.1-.46 5.9-3.48 '
    '8.05-5.95C21.5 13.5 22 11.9 22 10.16 22 5.66 17.5 2 12 2ZM7.5 12.9H5.62a.5.5 0 0 1-.5-.5V8.6a.5.5 0 0 1 '
    '1 0v3.3H7.5a.5.5 0 0 1 0 1Zm2.05-.5a.5.5 0 0 1-1 0V8.6a.5.5 0 0 1 1 0v3.8Zm4.2 0a.5.5 0 0 1-.9.3l-1.93-2.62v2.32a.5.5 '
    '0 0 1-1 0V8.6a.5.5 0 0 1 .9-.3l1.93 2.63V8.6a.5.5 0 0 1 1 0v3.8Zm3.13-2.4a.5.5 0 0 1 0 1h-1.38v.9h1.38a.5.5 0 0 1 '
    '0 1h-1.88a.5.5 0 0 1-.5-.5V8.6a.5.5 0 0 1 .5-.5h1.88a.5.5 0 0 1 0 1h-1.38v.9h1.38Z"/></svg>'
)
ICON_FORM = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true">'
    '<path d="M5 3.8h9.2L19 8.6V20.2H5z"/><path d="M14 3.8v5h5"/><path d="M8.2 12.6h7.6M8.2 16h5"/></svg>'
)
ICON_TEL = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true">'
    '<path d="M6.4 3.8h3l1.5 3.7-2 1.4a12 12 0 0 0 5.2 5.2l1.4-2 3.7 1.5v3a1.6 1.6 0 0 1-1.8 1.6C10.9 17.5 6.5 '
    '13.1 4.8 5.6A1.6 1.6 0 0 1 6.4 3.8Z"/></svg>'
)
ICON_INSTA = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true">'
    '<rect x="3.2" y="3.2" width="17.6" height="17.6" rx="5"/><circle cx="12" cy="12" r="4"/>'
    '<circle cx="17.2" cy="6.8" r="1.1" fill="currentColor" stroke="none"/></svg>'
)


# =========================================================
# <head>
# =========================================================
def build_head(page: str, cfg: dict) -> str:
    origin = base_origin()
    url = f"{origin}/" if page == "index.html" else f"{origin}/{page}"
    is_home = cfg.get("crumb") is None
    indexable = cfg.get("index", True)

    lines = [
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{cfg['title']}</title>",
        f'<meta name="description" content="{cfg["desc"]}">',
        '<meta name="theme-color" content="#14150f">',
        '<meta name="format-detection" content="telephone=no">',
    ]

    if PREVIEW:
        lines.append("<!-- 確認用URLのため検索エンジンには登録させません（本番公開時は PREVIEW=False） -->")
        lines.append('<meta name="robots" content="noindex, nofollow">')
    elif indexable:
        lines.append(f'<link rel="canonical" href="{url}">')
    else:
        lines.append('<meta name="robots" content="noindex, follow">')

    lines += [
        "",
        "<!-- OGP / Twitter -->",
        f'<meta property="og:type" content="{"website" if is_home else "article"}">',
        f'<meta property="og:site_name" content="{SITE["name"]}">',
        '<meta property="og:locale" content="ja_JP">',
        f'<meta property="og:title" content="{cfg["title"]}">',
        f'<meta property="og:description" content="{cfg["desc"]}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{origin}/{OG_IMAGE}">',
        f'<meta property="og:image:width" content="{OG_IMAGE_W}">',
        f'<meta property="og:image:height" content="{OG_IMAGE_H}">',
        '<meta name="twitter:card" content="summary_large_image">',
        "",
        "<!-- Icons -->",
        '<link rel="icon" href="assets/icon/favicon.svg" type="image/svg+xml">',
        '<link rel="apple-touch-icon" href="assets/icon/apple-touch-icon.png">',
        "",
        "<!-- Webフォントはローカル同梱（assets/fonts）。CDN配信に戻す方法は README.md を参照 -->",
        '<link rel="stylesheet" href="assets/css/fonts.css">',
        '<link rel="stylesheet" href="assets/css/style.css">',
    ]

    if is_home:
        lines.append('<link rel="preload" as="image" href="assets/img/hero.jpg" fetchpriority="high">')

    lines += [
        "",
        "<!-- JS有効時のみのスタイル切り替え -->",
        "<script>document.documentElement.classList.remove('no-js');</script>",
    ]

    for block in build_jsonld(page, cfg, url):
        lines.append('<script type="application/ld+json">')
        lines.append(json.dumps(block, ensure_ascii=False, indent=2))
        lines.append("</script>")

    lines.append("</head>")
    return "\n".join(lines)


def build_jsonld(page: str, cfg: dict, url: str) -> list:
    origin = base_origin()
    blocks = []

    if page == "index.html":
        blocks.append({
            "@context": "https://schema.org",
            "@type": "Store",
            "@id": f"{origin}/#store",
            "name": SITE["name"],
            "alternateName": "オーガストショップ",
            "description": "アメカジ・ブランド古着・アーカイブ・本格ヴィンテージの販売および買取。"
                           "対面買取のほか、宅配買取・LINE査定で全国に対応しています。",
            "url": f"{origin}/",
            "image": f"{origin}/{OG_IMAGE}",
            "logo": f"{origin}/assets/icon/apple-touch-icon.png",
            "telephone": SITE["tel"],
            "email": SITE["mail"],
            "currenciesAccepted": "JPY",
            "paymentAccepted": "現金, クレジットカード, 電子マネー, QRコード決済",
            "priceRange": "¥¥",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "JP",
                "postalCode": SITE["zip"],
                "addressRegion": SITE["address_region"],
                "addressLocality": SITE["address_city"],
                "streetAddress": SITE["address_street"],
            },
            "parentOrganization": {"@type": "Organization", "name": SITE["company_en"]},
            "sameAs": [SITE["instagram_url"]],
            "openingHoursSpecification": [{
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": ["Monday", "Tuesday", "Friday", "Saturday", "Sunday"],
                "opens": "13:00",
                "closes": "19:00",
            }],
        })
    elif cfg.get("crumb") and cfg.get("index", True):
        blocks.append({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "ホーム", "item": f"{origin}/"},
                {"@type": "ListItem", "position": 2, "name": cfg["crumb"], "item": url},
            ],
        })

    if cfg.get("faq"):
        blocks.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a},
                }
                for q, a in cfg["faq"]
            ],
        })

    return blocks


def line_anchor(cfg: dict) -> str:
    """LINE査定セクションを持たないページ（プライバシーポリシー・404）では
    トップページのセクションへ誘導する。"""
    return "#line" if cfg.get("line", True) else "index.html#line"


# =========================================================
# ヘッダー周り
# =========================================================
def build_chrome(page: str, cfg: dict) -> str:
    line_href = line_anchor(cfg)
    gnav = "\n      ".join(
        '<a href="{href}"{cur}><span>{en}</span><em>{jp}</em></a>'.format(
            href=n["href"],
            cur=' class="is-current" aria-current="page"' if n["href"] == page else "",
            en=n["en"], jp=n["jp"],
        )
        for n in SITE["nav"]
    )
    drawer_nav = "\n      ".join(
        '<a href="{href}"{cur}><span class="en">{en}</span><span class="jp">{jp}</span></a>'.format(
            href=n["href"],
            cur=' aria-current="page"' if n["href"] == page else "",
            en=n["en"], jp=n["jp"],
        )
        for n in SITE["nav"]
    )

    topbar = ""
    if SITE["topbar_text"]:
        topbar = f"""
<div class="topbar">
  <a href="{SITE['topbar_href']}" class="topbar__inner">
    <span class="topbar__tag">{SITE['topbar_tag']}</span>
    <span class="topbar__text">{SITE['topbar_text']}</span>
    <span class="topbar__arrow" aria-hidden="true">→</span>
  </a>
</div>
"""

    return f"""<a href="#top" class="skiplink">本文へスキップ</a>
{topbar}
<header class="header" id="header">
  <div class="header__inner">
    <a href="index.html" class="logo" aria-label="August Shop ホーム">
      <span class="logo__mark" aria-hidden="true"></span>
      <span class="logo__text">
        <span class="logo__name">August Shop</span>
        <span class="logo__sub">BUY &amp; SELL — ATSUGI</span>
      </span>
    </a>

    <nav class="gnav" aria-label="メインナビゲーション">
      {gnav}
    </nav>

    <div class="header__actions">
      <a href="form.html" class="btn btn--dark btn--sm"><span class="btn__icon">{ICON_FORM}</span>買取フォーム</a>
      <a href="{line_href}" class="btn btn--line btn--sm"><span class="btn__icon">{ICON_LINE}</span>LINE査定</a>
      <button class="burger" id="burger" type="button" aria-label="メニューを開く" aria-expanded="false" aria-controls="drawer">
        <span></span><span></span>
      </button>
    </div>
  </div>
</header>

<div class="drawer" id="drawer" aria-hidden="true">
  <nav class="drawer__nav" aria-label="メニュー">
      {drawer_nav}
  </nav>
  <div class="drawer__foot">
    <div class="drawer__btns">
      <a href="{line_href}" class="btn btn--line btn--block"><span class="btn__icon">{ICON_LINE}</span>LINEで査定する</a>
      <a href="form.html" class="btn btn--outline btn--block"><span class="btn__icon">{ICON_FORM}</span>買取フォームで見積り</a>
    </div>
    <p class="drawer__note">
      TEL <a href="{SITE['tel_link']}">{SITE['tel']}</a>／営業 {SITE['hours']}（定休日：{SITE['closed']}）
    </p>
  </div>
</div>"""


# =========================================================
# フッター周り
# =========================================================
def build_foot(page: str, cfg: dict) -> str:
    line_href = line_anchor(cfg)
    line_section = ""
    if cfg.get("line", True):
        line_section = f"""
<section class="linecta" id="line">
  <div class="container">
    <div class="linecta__inner">
      <div class="linecta__body">
        <p class="eyebrow eyebrow--light">LINE Assessment</p>
        <h2 class="linecta__title">写真を送るだけ。<br>24時間以内に概算査定をお返しします。</h2>
        <p class="linecta__text">
          友だち追加のうえ、①アイテム全体 ②ブランドタグ／品質表示 ③付属品 のお写真をお送りください。<br>
          ご相談・査定・キャンセルはすべて無料です。
        </p>
        <div class="linecta__actions">
          <a href="{SITE['line_url']}" class="btn btn--line btn--lg" target="_blank" rel="noopener"><span class="btn__icon">{ICON_LINE}</span>友だち追加して査定する</a>
          <a href="form.html" class="btn btn--outline btn--lg">フォームで見積りを依頼</a>
        </div>
        <p class="linecta__meta">LINE ID：<b>{SITE['line_id']}</b>　／　買取専用メール：<b>{SITE['mail']}</b></p>
      </div>
      <div class="linecta__qr">
        <div class="qr">
          <div class="qr__frame">
            <img src="assets/icon/line-qr.png" alt="August Shop 公式LINEの友だち追加用QRコード" width="300" height="300" loading="lazy" decoding="async">
          </div>
          <p>友だち追加</p>
        </div>
      </div>
    </div>
  </div>
</section>
"""

    return f"""{line_section}
<footer class="footer">
  <div class="container">
    <div class="footer__top">
      <div class="footer__brand">
        <span class="logo__name logo__name--lg">August Shop</span>
        <p class="footer__tagline">
          アメカジ・ブランド古着からアーカイブ、本格ヴィンテージまで。<br>
          長く愛せる一着に出会える場所を目指しています。
        </p>
        <dl class="footer__info">
          <div><dt>営業時間</dt><dd>{SITE['hours']}</dd></div>
          <div><dt>定休日</dt><dd>{SITE['closed']}</dd></div>
          <div><dt>TEL</dt><dd><a href="{SITE['tel_link']}">{SITE['tel']}</a></dd></div>
          <div><dt>住所</dt><dd>{SITE['address']}</dd></div>
        </dl>
        <div class="footer__sns">
          <a href="{SITE['instagram_url']}" target="_blank" rel="noopener">{ICON_INSTA}Instagram</a>
          <a href="{SITE['line_url']}" target="_blank" rel="noopener">{ICON_LINE}LINE</a>
        </div>
      </div>
      <nav class="footer__nav" aria-label="フッターナビゲーション">
        <div>
          <p class="footer__navhead">Buy</p>
          <a href="buy.html">買取について</a>
          <a href="buy.html#methods">買取方法（対面／宅配／LINE）</a>
          <a href="buy.html#ng">買取できないもの</a>
          <a href="buy.html#results">買取実績</a>
          <a href="buy.html#brands">取り扱いブランド</a>
          <a href="form.html">買取フォーム</a>
        </div>
        <div>
          <p class="footer__navhead">Shop</p>
          <a href="about.html">店舗紹介</a>
          <a href="shop.html">販売について</a>
          <a href="shop.html#access">アクセス</a>
          <a href="shop.html#payment">決済方法</a>
          <a href="restore.html">リペア・お直し</a>
          <a href="instagram.html">インスタグラム</a>
        </div>
        <div>
          <p class="footer__navhead">Information</p>
          <a href="about.html#company">会社概要</a>
          <a href="index.html#campaign">キャンペーン・クーポン</a>
          <a href="buy.html#faq">よくあるご質問</a>
          <a href="privacy.html">プライバシーポリシー</a>
          <a href="about.html#company">古物営業法に基づく表記</a>
        </div>
      </nav>
    </div>
    <div class="footer__bottom">
      <p class="footer__copy">© August Shop / SGN Co.,Ltd. All Rights Reserved.</p>
      <p class="footer__mock">{SITE['license']}</p>
    </div>
  </div>
</footer>

<div class="actionbar">
  <a href="{line_href}" class="actionbar__btn actionbar__btn--line">
    <span class="actionbar__icon">{ICON_LINE}</span>
    <span class="actionbar__label"><b>LINE査定</b><small>写真を送るだけ</small></span>
  </a>
  <a href="form.html" class="actionbar__btn actionbar__btn--form">
    <span class="actionbar__icon">{ICON_FORM}</span>
    <span class="actionbar__label"><b>買取フォーム</b><small>HP内で完結</small></span>
  </a>
  <a href="{SITE['tel_link']}" class="actionbar__btn actionbar__btn--tel">
    <span class="actionbar__icon">{ICON_TEL}</span>
    <span class="actionbar__label"><b>お電話</b><small>{SITE['tel']}</small></span>
  </a>
</div>

<script src="assets/js/main.js" defer></script>"""


# =========================================================
# 置換処理
# =========================================================
BUILDERS = {"head": build_head, "chrome": build_chrome, "foot": build_foot}


def replace_region(html: str, key: str, body: str, page: str) -> str:
    pattern = re.compile(
        r"(<!-- @common:%s -->)(.*?)(<!-- /@common:%s -->)" % (key, key),
        re.DOTALL,
    )
    if not pattern.search(html):
        raise SystemExit(f"[error] {page}: マーカー <!-- @common:{key} --> が見つかりません")
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(3)}", html, count=1)


def render(page: str, cfg: dict, html: str) -> str:
    for key, builder in BUILDERS.items():
        html = replace_region(html, key, builder(page, cfg), page)
    return html


def build_robots() -> str:
    if PREVIEW:
        return (
            "# 確認用URLのため、検索エンジンによるクロールを禁止しています。\n"
            "# 本番公開時は tools/sync-common.py の PREVIEW を False にして再実行してください。\n"
            "User-agent: *\n"
            "Disallow: /\n"
        )
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /404.html\n"
        "\n"
        f"Sitemap: {SITE['origin']}/sitemap.xml\n"
    )


def build_sitemap() -> str:
    origin = base_origin()
    rows = []
    for page, cfg in PAGES.items():
        if not cfg.get("index", True):
            continue
        loc = f"{origin}/" if page == "index.html" else f"{origin}/{page}"
        rows.append(
            "  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <changefreq>{cfg.get('changefreq', 'monthly')}</changefreq>\n"
            f"    <priority>{cfg.get('priority', '0.5')}</priority>\n"
            "  </url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows)
        + "\n</urlset>\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="共通パーツとメタ情報を全ページへ同期します")
    parser.add_argument("--check", action="store_true", help="書き換えずに差分の有無だけ確認する")
    args = parser.parse_args()

    changed = []
    for page, cfg in PAGES.items():
        path = ROOT / page
        if not path.exists():
            print(f"[skip] {page} がありません")
            continue
        before = path.read_text(encoding="utf-8")
        after = render(page, cfg, before)
        if before != after:
            changed.append(page)
            if not args.check:
                path.write_text(after, encoding="utf-8")

    for name, content in (("sitemap.xml", build_sitemap()), ("robots.txt", build_robots())):
        path = ROOT / name
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            changed.append(name)
            if not args.check:
                path.write_text(content, encoding="utf-8")

    if args.check:
        if changed:
            print("要同期: " + ", ".join(changed))
            return 1
        print("すべて同期済みです")
        return 0

    print("更新: " + (", ".join(changed) if changed else "なし（すべて同期済み）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
