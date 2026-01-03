# ホロジュールAPI 配信情報フィールド一覧

## エンドポイント
```
GET https://schedule.hololive.tv/api/list/7
```
※ `7` は取得日数

---

## レスポンス構造

```json
{
  "dateGroupList": [
    {
      "displayDate": "01.03",
      "datetime": "2026/01/03 00:00:00",
      "videoList": [ /* 配信オブジェクトの配列 */ ]
    }
  ]
}
```

---

## 配信オブジェクト (videoList内の1要素)

```json
{
  "displayDate": "12:00",
  "datetime": "2026/01/03 12:00:00",
  "isLive": true,
  "platformType": 1,
  "url": "https://www.youtube.com/watch?v=xxxxx",
  "thumbnail": "https://img.youtube.com/vi/xxxxx/mqdefault.jpg",
  "title": "【雑談】あけましておめでとう【○○○○/ホロライブ】",
  "name": "○○○○",
  "talent": {
    "name": "○○○○",
    "iconImageUrl": "https://yt3.ggpht.com/xxxxx=s88-c-k-c0x00ffffff-no-rj"
  },
  "collaboTalents": [
    {
      "name": "コラボ相手A",
      "iconImageUrl": "https://yt3.ggpht.com/xxxxx=s88-c-k-c0x00ffffff-no-rj"
    }
  ]
}
```

---

## フィールド詳細

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `displayDate` | string | 表示用の時刻（"12:00"形式） |
| `datetime` | string | フルの日時（"YYYY/MM/DD HH:MM:SS"）**※JST固定** |
| `isLive` | boolean | **配信開始したらtrue、配信終了したらfalse** |
| `platformType` | number | 配信プラットフォーム（**無視してOK**） |
| `url` | string | 配信ページのURL |
| `thumbnail` | string | サムネイル画像URL（mqdefault=320x180） |
| `title` | string | 配信タイトル |
| `name` | string | タレント名（talent.nameと同じ） |
| `talent` | object | メイン配信者の情報 |
| `talent.name` | string | **サムネイル画像に表示されてるタレント名** |
| `talent.iconImageUrl` | string | タレントアイコンURL |
| `collaboTalents` | array | コラボ参加者リスト（空配列=ソロ配信） |

---

## isLive の挙動

```
枠立て → isLive: false
配信開始 → isLive: true  ← ここで通知出す！
配信終了 → isLive: false
```

---

## サムネイル解像度

YouTubeサムネイルは以下の解像度が利用可能：

| 名前 | サイズ | URL例 |
|------|--------|-------|
| default | 120x90 | `https://img.youtube.com/vi/{ID}/default.jpg` |
| mqdefault | 320x180 | `https://img.youtube.com/vi/{ID}/mqdefault.jpg` |
| hqdefault | 480x360 | `https://img.youtube.com/vi/{ID}/hqdefault.jpg` |
| sddefault | 640x480 | `https://img.youtube.com/vi/{ID}/sddefault.jpg` |
| maxresdefault | 1280x720 | `https://img.youtube.com/vi/{ID}/maxresdefault.jpg` |

※ APIは `mqdefault` を返すが、必要に応じて差し替え可能

---

## タイムゾーン

**JST (UTC+9) 固定**で処理する。
