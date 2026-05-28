# 滘西洲南場記分器 · 雲端部署指南（Render）

部署後會得到固定網址，例如 `https://kau-sai-golf.onrender.com`，  
**手機用 4G 也能打開**，可貼到 WhatsApp 群。

---

## 第一步：上傳到 GitHub

1. 登入 https://github.com  →  **New repository**
2. 名稱例如：`kau-sai-golf` → **Create repository**
3. 在本機終端機執行（把 `你的帳號` 換成你的 GitHub 用戶名）：

```bash
cd ~/Desktop/Python高爾夫
git init
git add .
git commit -m "滘西洲南場高爾夫記分器網頁版"
git branch -M main
git remote add origin https://github.com/你的帳號/kau-sai-golf.git
git push -u origin main
```

---

## 第二步：Render 部署

1. 登入 https://render.com （可用 GitHub 登入）
2. **New +** → **Blueprint**
3. 連接剛才的 GitHub 倉庫 `kau-sai-golf`
4. Render 會讀取 `render.yaml` → **Apply**
5. 等待約 3～5 分鐘，狀態變 **Live**
6. 點開網址，例如 `https://kau-sai-golf.onrender.com`

---

## 第三步：記下同步密鑰

1. 在 Render 點你的服務 → **Environment**
2. 找到 **`SYNC_SECRET`** → 複製數值（只給管理員，不要貼到群組）

---

## 之後每次打完球

### 方式 A：網頁直接錄分（推薦）

1. 打開 `https://你的網址.onrender.com/score`
2. 填球友名字 → 逐洞記分（可點 Par / +1 快捷鍵）
3. 填 **管理員密鑰**（與 Render 的 `SYNC_SECRET` 相同）→ 存檔
4. 群友重新整理首頁即可看到

### 方式 B：本機錄分再同步

```bash
cd ~/Desktop/Python高爾夫
python3 golf_score.py   # 選 2 多人記分
export DEPLOY_URL="https://你的網址.onrender.com"
export SYNC_KEY="貼上 SYNC_SECRET"
python3 sync_rounds.py
```

---

## 會員帳號為什麼會「每次更新就消失」？

Render **免費版 Web 服務的檔案系統是暫存的**：每次重新部署或重啟，容器內的 `app.db` 會被清空。  
`app.db` 又在 `.gitignore` 裡，**不會跟著 Git 上傳**，所以線上每次都是「空資料庫」→ 舊帳號不存在，只能重新註冊。

**解法（已寫入 `render.yaml`）**：使用 **Render PostgreSQL**，透過環境變數 `DATABASE_URL` 存會員資料。資料庫與 Web 服務分開，部署程式碼**不會**刪除使用者。

### 若你早已部署過（沒有 Postgres）

1. Render Dashboard → **New +** → **PostgreSQL**（免費方案即可）
2. 建立後，複製 **Internal Database URL** 或 **External Database URL**
3. 打開你的 **Web 服務** → **Environment** → 新增：
   - `DATABASE_URL` = 剛才的連線字串
   - 確認 `SECRET_KEY` 已存在且**不要**每次部署都刪掉重產（否則已登入 cookie 會失效，但帳號仍在）
4. **Manual Deploy** 一次，讓程式安裝 `psycopg2-binary` 並連到新庫
5. **第一次接上 Postgres 後資料庫是空的**，球友需再註冊一次；之後每次更新程式碼，帳號都會保留

### 本機開發

不設 `DATABASE_URL` 時仍使用專案目錄的 `app.db`，與線上資料庫**分開**。

---

## 注意

- **免費版**約 15 分鐘沒人訪問會休眠，第一次打開可能要等 30～50 秒喚醒。
- 雲端資料存在伺服器；本機 `rounds.json` 與雲端要以 `sync_rounds.py` 同步。
- 上傳的**頭像檔**若放在容器本機，免費版部署後也可能遺失；長期可改雲端儲存或 Render 持久化磁碟（`INSTANCE_DATA_DIR`）。
