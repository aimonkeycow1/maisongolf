# Maison Golf · 部署說明（極簡測試版）

目前版本：**零登入 + 本地儲存**的記分工具。線上網址：https://maisongolf.onrender.com

## 這個版本怎麼運作

- **不需要註冊或登入**，打開網頁即可記分。
- **場次與成績資料存在使用者「瀏覽器 localStorage」**，不存在伺服器。
  - 換瀏覽器／換裝置／清除瀏覽器資料 → 該裝置的紀錄會消失（這是測試版的預期行為）。
  - 伺服器重部署不影響使用者資料（因為資料在用戶端）。
- 因此**不需要資料庫**；容器內的 SQLite 只是框架初始化用，可隨時清空。

## 部署到 Render

已透過 `render.yaml`（Blueprint）設定，推到 GitHub 後 Render 會自動：

- Build：`pip install -r requirements.txt`
- Start：`gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`
- Python：`3.12.7`

啟動後可在 **Render → Logs** 看到開機橫幅，內含目前的 OCR 模式與儲存方式。

## 拍照讀 Par（OCR）

| 環境變數 | 測試（預設） | 切換真實辨識 |
|---|---|---|
| `OCR_MOCK` | `true`（回模擬 Par） | `false` |
| `XAI_API_KEY` | 不需要 | 填入 xAI 金鑰 |

切換真實 Grok Vision：在 Render → Environment 設 `XAI_API_KEY`，並把 `OCR_MOCK` 改為 `false`，手動 Deploy 一次即可。

> 模式判斷：`OCR_MOCK` 預設為 `true`。只有在 `OCR_MOCK=false` 且有 `XAI_API_KEY` 時才會呼叫真實辨識；若 `false` 但未設金鑰，前端會提示用戶改用手動模板。

## 本機開發

```bash
pip install -r requirements.txt
python app.py            # http://127.0.0.1:5050
OCR_MOCK=true python app.py   # 本機也用模擬 OCR 測試流程
```
