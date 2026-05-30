# Maison Golf · 雲端部署指南（Render）

部署後得到固定網址，例如 `https://kau-sai-golf.onrender.com`，  
**手機用 4G 也能打開**，可貼到 WhatsApp 群。

---

## ⭐ 上線前完整檢查清單（Go-Live Checklist）

> 每次部署前後請逐項確認，攸關資料永久保存與用戶體驗。

### 🔒 資料永久保存（最重要）
- [ ] `DATABASE_URL` 已設定且連到 **Render PostgreSQL**（Web 服務 → Environment 確認）。  
      缺少時 fallback 到容器內 SQLite，**每次部署全部清空**。
- [ ] PostgreSQL 資料庫**未被刪除**、狀態 Active（免費方案到期前保留）。
- [ ] 所有資料表已自動建立（`db.create_all()` 在 app 啟動時執行），包含：  
      `users`、`friend_requests`、`challenges`、`golf_rounds`、`round_participants`、`hole_scores`

### 🔑 帳號與登入
- [ ] `SECRET_KEY` 已固定（首次 `generateValue` 後在 Dashboard 鎖定，勿每次部署重產；  
      變動會登出已登入用戶，但資料不遺失）。
- [ ] `dev_tools.py` 在生產環境**自動關閉**（`RENDER=true` 時測試面板不可見，確認首頁無「測試」按鈕）。

### 🖼️ 頭像與媒體
- [ ] Cloudinary 三個環境變數已設定：`CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET`。  
      不填則頭像存容器內，**部署後消失**。

### 🤖 AI 教練
- [ ] 若要啟用 Grok API：`XAI_API_KEY` 已設定。  
      不設定時使用本地深度分析（功能完整，無需 API）。

### 🧪 功能煙霧測試（部署後點一遍）

| 路由 | 預期行為 |
|------|---------|
| `/`（未登入） | 看到公開落地頁、「立即登入」CTA |
| `/register` | 填球友名稱 + 密碼 → 成功跳首頁 |
| `/login` / 登出 | 正常跳轉，登出後 Cookie 清除 |
| `/` (已登入) | 看到 Momentum Strip、好友動態 Feed、歷史場次 |
| `/score` | 選球場（含清水灣、粉嶺）→ 逐洞記分 → 實時對決欄更新 |
| `/round/<id>` | 成績卡 + AI 教練 + 同球場跨場次比較 + 分享圖卡 |
| `/progress` | 差點指數 + 趨勢圖 + 弱點洞熱力圖 + 好友差點排行榜 + 挑戰系統 |
| `/year-review` | 2026 年度回顧頁面正常渲染 |
| `/friends` | 搜尋 / 邀請 / 好友列表 |
| `/challenge/my` | 返回 JSON `{"ok": true, "challenges": [...]}` |
| `/stats` | 全域統計頁正常 |
| `/profile` | 個人資料、頭像上傳 |

---

## 第一步：上傳到 GitHub

```bash
cd ~/Desktop/Python高爾夫
git init
git add .
git commit -m "Maison Golf — 完整版上線"
git branch -M main
git remote add origin https://github.com/你的帳號/kau-sai-golf.git
git push -u origin main
```

> `rounds.json`、`simulate_users.py`、`sim_report.json`、`app.db` 已加入 `.gitignore`，不會上傳。

---

## 第二步：Render Blueprint 部署

1. 登入 https://render.com（可用 GitHub 登入）
2. **New +** → **Blueprint**
3. 連接剛才的 GitHub 倉庫
4. Render 讀取 `render.yaml` → **Apply**
5. 等待約 3～5 分鐘，狀態變 **Live**
6. 首次部署後在 **Environment** 把以下三個「選填」變數補上（見下方）：
   - `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET`
   - （可選）`XAI_API_KEY`

---

## 第三步：鎖定 SECRET_KEY

1. 服務 → **Environment** → 找到 `SECRET_KEY`
2. 複製值 → 刪除原本的 `generateValue` 設定 → 改為 `value: "剛才複製的值"`
3. **Save Changes**（不需重新部署，下次部署自動使用固定值）

---

## 之後每次更新程式碼

```bash
cd ~/Desktop/Python高爾夫
git add .
git commit -m "說明這次改了什麼"
git push
```

Render 連接 GitHub 後會**自動偵測 push → 重新部署**，約 2～3 分鐘，資料庫資料**完整保留**。

---

## 功能架構速覽

### 核心記分
- 多球場多梯台（香港 KSC 三場 + 清水灣 + 粉嶺 Eden + 馬來西亞 + 泰國）
- Slope / Course Rating 已錄入，WHS 差點計算更準確
- 逐洞記分 + 自動存草稿（可中途離開）
- **實時對決欄**：記分過程中即時更新各球手總桿排名

### 成長引擎
- WHS 風格差點指數（最佳 N 場）+ 趨勢圖
- **逐洞弱點熱力圖**：18 格彩色熱力格 + 強/弱洞自動標出 + 4 種規律偵測
- **跨場次比較**：同球場上次 vs 這次逐洞對比
- **年度回顧**（`/year-review`）：全年統計、月份熱力圖、桿數分布

### 社交成癮
- **好友動態 Feed**：首頁即時顯示球友最新動態
- **差點排行榜**：好友間名次對比（🥇🥈🥉）
- **差點挑戰**：30 天進步競賽，追蹤誰降得更多
- 賽後慶祝彈窗（彩帶）+ 里程碑慶祝
- 可分享圖卡（Battle Report Card + 進步曲線卡）

### 基礎設施
- Flask + SQLAlchemy（SQLite 本機 / PostgreSQL 線上）
- Cloudinary 頭像持久化
- B+ 設計語言（深綠金 / Playfair Display / Aurora 背景）
- 本機開發測試面板（`/dev/test`）— **生產環境自動關閉**

---

## 資料永久保存原理

| 環境 | 資料庫 | 重新部署後 |
|------|--------|-----------|
| Render（已設 DATABASE_URL）| PostgreSQL | ✅ 完整保留 |
| Render（未設 DATABASE_URL）| 容器內 SQLite | ❌ 每次清空 |
| 本機開發 | `app.db`（SQLite） | ✅ 本機保留 |

---

## 常見問題

### 免費版休眠
免費 Render Web 服務約 15 分鐘無訪問會休眠，第一次打開等 30～50 秒喚醒正常。

### Challenges 表不存在
新版新增了 `challenges` 資料表，首次部署到有此代碼的版本時，`db.create_all()` 會自動建立，無需手動執行 migration。

### 頭像部署後消失
未設定 Cloudinary 三個環境變數。請依本文第一步「上線前檢查清單」補設。

### AI 教練沒有反應
未設定 `XAI_API_KEY`，系統使用本地深度分析（功能完整）。若要升級到 Grok API，在 Environment 添加 `XAI_API_KEY`。
