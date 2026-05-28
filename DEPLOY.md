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

## 打球紀錄存在哪裡？

**Render 正式環境**：所有場次寫入 **PostgreSQL**（`golf_rounds`、`round_participants`、`hole_scores` 表），重新部署後紀錄**不會消失**。請確認 Web 服務已設定 `DATABASE_URL`。

**本機開發**：無 `DATABASE_URL` 時，帳號在 `app.db`、打球紀錄也在同一 SQLite 檔。首次啟動若專案內有 `rounds.json`，會自動匯入資料庫一次。

`rounds.json` 僅作本機備份／CLI 相容，**不再作為正式儲存**。

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
- **頭像**請使用 **Cloudinary**（見下方），勿只放在 `static/uploads/avatars/`。

---

## 頭像為什麼部署後會消失？

頭像若存在容器內 `static/uploads/avatars/`，與 `app.db` 一樣屬於**暫存檔案系統**，每次 Render 重新部署都會被清空。

### 方案 A（推薦）：Cloudinary

業界標準做法：圖片存在 Cloudinary，資料庫只存 URL 與 `public_id`，經 CDN 載入快、部署後不消失。

#### 1. 註冊 Cloudinary

1. 前往 https://cloudinary.com 註冊（免費額度足夠個人／小團隊）
2. Dashboard → **API Keys** 記下：
   - **Cloud name**
   - **API Key**
   - **API Secret**

#### 2. Render 環境變數

Web 服務 → **Environment** → **Add Environment Variable**：

| 變數名稱 | 說明 |
|----------|------|
| `CLOUDINARY_CLOUD_NAME` | Dashboard 的 Cloud name |
| `CLOUDINARY_API_KEY` | API Key |
| `CLOUDINARY_API_SECRET` | API Secret（勿公開、勿 commit） |

儲存後 **Manual Deploy** 一次。

#### 3. 行為說明

- 會員在「個人設定」上傳頭像 → 壓縮為 256×256 JPEG → 上傳至 Cloudinary 資料夾 `maisongolf/avatars/user_{id}`
- 資料庫欄位：`avatar_url`（CDN 網址）、`avatar_public_id`、`avatar_revision`（快取破壞）
- 未設定 Cloudinary 時，本機開發仍寫入 `static/uploads/avatars/`（僅供本機測試）
- 若線上曾用本機頭像、DB 仍有 `avatar_path` 但無 `avatar_url`，**下次啟動**會嘗試自動上傳至 Cloudinary（需三個環境變數已設定）

#### 4. 舊本機頭像手動遷移（可選）

已部署且頭像已遺失的帳號，只能請使用者**重新上傳**。若容器內檔案還在、DB 仍有 `avatar_path`，重啟應用會自動遷移。

---

### 方案 B（備選）：Render Persistent Disk

若不想用外部服務，可為 Web 服務掛載**持久化磁碟**：

1. Render Dashboard → 你的 **Web 服務** → **Disks** → **Add Disk**
2. 例如掛載路徑 `/var/data`、大小 1GB（依方案）
3. **Environment** 新增：`INSTANCE_DATA_DIR` = `/var/data`
4. 程式會把頭像寫到 `/var/data/avatars/`（見 `avatar_service.py`），重啟後保留

注意：磁碟與服務綁定、免費方案可能需付費；多實例／擴展時不如 Cloudinary 單純。正式環境仍建議 **方案 A**。
