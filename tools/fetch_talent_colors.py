#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ホロライブ非公式wiki からタレントカラー情報を抽出するツール

使い方:
    pip install requests beautifulsoup4
    python fetch_talent_colors.py

出力:
    output/talent-colors.json
"""

import json
import re
import time
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

# 設定
BASE_URL = "https://seesaawiki.jp/hololivetv"
TOP_PAGE_URL = f"{BASE_URL}/"
REQUEST_DELAY = 1.0  # リクエスト間隔（秒）
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "talent-colors.json"

# HTTPヘッダー
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
}

# 除外するページ名のパターン（部分一致）
EXCLUDE_PATTERNS = [
    # メニュー・管理系
    "サイト内検索", "メンバー一覧", "ページ一覧", "トップページ", "総合案内",
    "FAQ", "管理用", "掲示板", "編集者向け", "wiki編集", "sandbox", "基本的なwiki",
    "補助ツール", "編集作業", "編集予定", "注意事項",
    # 期生・グループページ
    "0期生", "1期生", "2期生", "3期生", "4期生", "5期生", "6期生",
    "ID1期生", "ID2期生", "ID3期生",
    "ゲーマーズ", "Myth", "Promise", "Advent", "Justice", "Council",
    "ReGLOSS", "FLOW GLOW", "Project:HOPE",
    # 組織・公式
    "ホロライブ", "hololive", "COVER", "hololivepro", "holoAN",
    "YAGOO", "友人A", "春先のどか", "井月みちる", "花園さやか", "風白ゆき", "Omega",
    # 一覧・まとめ系
    "早見表", "衣装一覧", "サイン一覧", "ハッシュタグ", "メンバーシップ",
    "実況ゲーム", "活動経歴", "ライブイベント", "実績一覧", "登録者数",
    "コンビ", "ユニット", "記念配信", "フルトラ", "配信内記録",
    "流行", "企画配信", "飲食物", "実写配信", "同時視聴", "ASMR",
    "歌唱楽曲", "歌ってみた", "歌枠", "楽器演奏", "歌リレー", "カラオケ",
    "コラボ", "配信環境", "配信セット", "動画一覧", "記念日", "達成", "ミリオン",
    "年表", "エピソード", "元ネタ", "オリジナルソング", "ディスコグラフィ",
    "音ゲー", "ファンミ", "シティ", "年末年始", "EXPO", "サマー",
    "ボイス", "グッズ", "公式配布", "ホロアース", "メディア出演", "インタビュー",
    "オルタナティブ", "ERROR", "Blue Journey", "ホロウィッチ", "ENigmatic",
    "ドリームス", "holo Indie", "もちぽよ", "地域関連", "ロケ企画", "雑多",
    "交友関係", "コミケ", "bilibili", "公式リンク", "ペンライト",
    # 語録・関連語
    "語録", "関連語",
    # 個別詳細ページ
    "衣装詳細", "歌唱曲", "BGM",
    # ゲームタイトル
    "Minecraft", "ARK", "Rust", "GTA", "人狼",
    # その他
    "タレント別ページ", "ホロプロ", "中国",
]

# 完全一致で除外する名前
EXCLUDE_EXACT = {
    "ID公式", "EN公式", "ReGLOSS公式", "FLOW GLOW公式",
    "カバー株式会社", "holoAN公式", "ホロアース", "ホロライブドリームス",
    "hololive OFFICIAL CARD GAME【公式】", "hololive_OCG_EN",
}


def fetch_page(url: str) -> str | None:
    """ページを取得"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except requests.RequestException as e:
        print(f"  ✗ 取得失敗: {e}")
        return None


def should_exclude(name: str) -> bool:
    """除外すべき名前かどうか判定"""
    # 完全一致チェック
    if name in EXCLUDE_EXACT:
        return True
    
    # 部分一致チェック
    for pattern in EXCLUDE_PATTERNS:
        if pattern in name:
            return True
    
    # 絵文字のみの名前は除外
    if not re.search(r'[a-zA-Zぁ-んァ-ヴー一-龥]', name):
        return True
    
    # 名前が空または短すぎる場合は除外
    if len(name) < 2:
        return True
    
    return False


def get_talent_urls() -> list[dict]:
    """トップページからタレントURL一覧を取得"""
    print("=" * 60)
    print("Step 1: タレントURL一覧を取得中...")
    print("=" * 60)
    
    html = fetch_page(TOP_PAGE_URL)
    if not html:
        print("トップページの取得に失敗しました")
        return []
    
    soup = BeautifulSoup(html, "html.parser")
    
    # user-area内のリンクを取得
    user_area = soup.find("div", class_="user-area")
    if not user_area:
        print("user-areaが見つかりません")
        return []
    
    talents = []
    seen_urls = set()
    
    # タレントページへのリンクを抽出
    # パターン: https://seesaawiki.jp/hololivetv/d/XXXXX
    pattern = re.compile(r"^https://seesaawiki\.jp/hololivetv/d/.+$")
    
    for link in user_area.find_all("a", href=pattern):
        url = link.get("href")
        
        # リンクテキストを取得（絵文字を除去してクリーンな名前を取得）
        raw_text = link.get_text(strip=True)
        
        # 絵文字を除去して名前だけ抽出
        # 絵文字は名前の前にあることが多いので、日本語/英語の文字列を抽出
        name = re.sub(r'^[^\w\s]*', '', raw_text, flags=re.UNICODE).strip()
        if not name:
            name = raw_text
        
        # 重複スキップ
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        # 除外判定
        if should_exclude(name):
            continue
        
        # ルビタグが含まれている場合、表示テキストを使用
        # 例: <ruby><rb>星街</rb><rt>ほしまち</rt></ruby>すいせい → 星街すいせい
        
        talents.append({
            "name": name,
            "url": url
        })
    
    print(f"  → {len(talents)} 件のタレントURLを取得しました")
    
    # デバッグ用：取得したタレント一覧を表示
    print("\n取得したタレント一覧:")
    for i, t in enumerate(talents, 1):
        print(f"  {i:3d}. {t['name']}")
    print()
    
    return talents


def extract_colors_from_page(html: str) -> dict | None:
    """ページHTMLからカラーコード情報を抽出"""
    soup = BeautifulSoup(html, "html.parser")
    
    colors = {
        "official_color1": None,
        "official_color2": None,
        "holodule_color": None
    }
    
    # 公式サイトでのタレント背景色を探す
    for th in soup.find_all("th"):
        th_text = th.get_text(strip=True)
        
        if "公式サイトでのタレント背景色" in th_text:
            # 同じtrのtdを取得（1つ目の色）
            tr = th.find_parent("tr")
            if tr:
                td = tr.find("td")
                if td:
                    # tdのテキストからカラーコードを抽出
                    color_match = re.search(r'#[0-9A-Fa-f]{6}', td.get_text())
                    if color_match:
                        colors["official_color1"] = color_match.group().upper()
                
                # 次のtrを取得（2つ目の色）
                next_tr = tr.find_next_sibling("tr")
                if next_tr:
                    td2 = next_tr.find("td")
                    if td2:
                        color_match = re.search(r'#[0-9A-Fa-f]{6}', td2.get_text())
                        if color_match:
                            colors["official_color2"] = color_match.group().upper()
        
        elif "ホロジュール外枠の色" in th_text:
            # 同じtrのtdを取得
            tr = th.find_parent("tr")
            if tr:
                td = tr.find("td")
                if td:
                    color_match = re.search(r'#[0-9A-Fa-f]{6}', td.get_text())
                    if color_match:
                        colors["holodule_color"] = color_match.group().upper()
    
    # 少なくとも1つのカラーが取得できた場合のみ返す
    if any(colors.values()):
        return colors
    return None


def fetch_talent_colors(talents: list[dict]) -> list[dict]:
    """各タレントページからカラー情報を取得"""
    print("\n" + "=" * 60)
    print("Step 2: 各タレントページからカラー情報を取得中...")
    print("=" * 60)
    
    results = []
    total = len(talents)
    
    for i, talent in enumerate(talents, 1):
        name = talent["name"]
        url = talent["url"]
        
        print(f"[{i}/{total}] {name}...", end=" ", flush=True)
        
        html = fetch_page(url)
        if not html:
            print("スキップ")
            time.sleep(REQUEST_DELAY)
            continue
        
        colors = extract_colors_from_page(html)
        if colors:
            result = {
                "name": name,
                "official_color1": colors["official_color1"],
                "official_color2": colors["official_color2"],
                "holodule_color": colors["holodule_color"]
            }
            results.append(result)
            print(f"✓ {colors['official_color1']} / {colors['official_color2']} / {colors['holodule_color']}")
        else:
            print("カラー情報なし")
        
        time.sleep(REQUEST_DELAY)
    
    return results


def save_results(results: list[dict]):
    """結果をJSONファイルに保存"""
    print("\n" + "=" * 60)
    print("Step 3: 結果を保存中...")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"  → {OUTPUT_FILE} に保存しました")
    print(f"  → {len(results)} 件のタレントカラー情報を取得しました")


def main():
    """メイン処理"""
    print("\n🎨 ホロライブ タレントカラー抽出ツール 🎨\n")
    
    # Step 1: タレントURL一覧を取得
    talents = get_talent_urls()
    if not talents:
        print("タレントが見つかりませんでした")
        return
    
    # Step 2: 各タレントページからカラー情報を取得
    results = fetch_talent_colors(talents)
    
    # Step 3: 結果を保存
    if results:
        save_results(results)
        print("\n✨ 完了しました！ ✨\n")
    else:
        print("\nカラー情報を取得できませんでした")


if __name__ == "__main__":
    main()
