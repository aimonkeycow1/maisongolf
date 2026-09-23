# 球場計分（Vite + React）

手機下場記桿 SPA。

本目錄是正式產品前端；repo 根目錄的 Flask 為舊版，未改動。

## 開發

```bash
cd web
npm install
npm run dev
```

## 建置／預覽

```bash
cd web
npm install
npm run build
npm run preview
```

Vercel：以 repo 根目錄的 `vercel.json` 建置 `web/`，或把專案 Root Directory 設為 `web`。

## 資料放哪、限制是什麼（定案）

| 項目 | 說明 |
|------|------|
| **主存放** | 瀏覽器 **IndexedDB**（資料庫名 `golf-scorekeeper`） |
| **鏡像／遷移** | `localStorage` 鍵 `golf-scorekeeper-v1`（寫穿鏡像；舊資料首次開啟會遷入 IDB） |
| **自動歸檔** | 「結束本輪」→ `status: completed` + `finishedAt` |
| **換機／清快取** | 本機資料會消失 → 成績庫「匯出封存／匯入封存」JSON |
| **目標桿數** | 預設 **95**（對齊「先穩在 95 內」），介面可改 |
| **雲端同步** | **本輪不做**（後續選項） |

## 成績庫與分析

- 首頁 → **成績庫**：日期塊、球場、洞數、總桿、相對目標（`+N`／`−N`／達標）
- 空庫時種子滘西洲東場示範（標「示範」）
- 計分卡底部：**弱項分析**（總推桿／GIR 上果嶺率／球道命中／柏忌及以上洞、各洞推桿數、提示）

畫面方向對齊創意總監 `golf-score-vision` 演示，記分主流程不重做。

## 手動驗收

1. 開始新一輪（可選滘西洲東場、9／18、多人）→ 記幾洞（含推桿／球道／GIR）→ 結束本輪
2. 重新整理或關閉再開 → 同一裝置在「已結束／成績庫」可找回
3. 成績庫可瀏覽歷史、改目標（預設 95）、匯出／匯入 JSON 封存
4. 打開計分卡可見弱項分析（演示稿風格）
5. 記分主流程（9／18、多人、球場預設記憶、教練欄位、點按與數字輸入）仍可用。沒有語音或麥克風入口。

可選自動化：`npm run build && npm run preview` 後 `node scripts/smoke.mjs`
