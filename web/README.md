# 球場計分（Vite + React）

手機下場記桿 SPA。資料存在瀏覽器 **localStorage**（鍵名 `golf-scorekeeper-v1`）。

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
npm run build
npm run preview
```

Vercel：以 repo 根目錄的 `vercel.json` 建置 `web/`，或把專案 Root Directory 設為 `web`。

## 資料放哪、限制是什麼

| 項目 | 說明 |
|------|------|
| 存放 | 瀏覽器 `localStorage` · `golf-scorekeeper-v1` |
| 自動歸檔 | 「結束本輪」後 `status: completed` + `finishedAt`，寫入同一封存 |
| 換機／清快取 | 本機資料會消失 → 請用成績庫「匯出封存／匯入封存」搬移 |
| 雲端帳號 | 本版未做（避免阻斷演示）；之後若要再接 |

## 成績庫與分析

- 首頁 → **成績庫**：跨局列表（日期、球場、總桿、相對目標預設 95）
- 空庫時會種子一筆滘西洲東場示範（標「示範」）
- 計分卡底部：**弱項分析**（總推桿／GIR%／球道%／柏忌+洞、推桿圖、提示）

## 手動驗收

1. 開始新一輪（可選滘西洲東場、9／18、多人）→ 記幾洞（含推桿／球道／GIR）→ 結束本輪
2. 重新整理或關閉再開 → 同一裝置在「已結束／成績庫」可找回
3. 成績庫可瀏覽歷史、改目標、匯出／匯入 JSON 封存
4. 打開計分卡可見弱項分析
5. 記分主流程（9／18、多人、球場預設記憶、教練欄位、語音）仍可用

可選自動化：`npm run build && npm run preview` 後 `node scripts/smoke.mjs`
