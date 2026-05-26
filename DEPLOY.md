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

## 之後每次打完球（本機錄分 → 同步雲端）

```bash
cd ~/Desktop/Python高爾夫

# 1. 本機錄分（和以前一樣）
python3 golf_score.py   # 選 2 多人記分

# 2. 上傳到雲端（把網址和密鑰換成你的）
export DEPLOY_URL="https://kau-sai-golf.onrender.com"
export SYNC_KEY="貼上 SYNC_SECRET"
python3 sync_rounds.py
```

群友重新整理網頁即可看到新成績。

---

## 注意

- **免費版**約 15 分鐘沒人訪問會休眠，第一次打開可能要等 30～50 秒喚醒。
- 雲端資料存在伺服器；本機 `rounds.json` 與雲端要以 `sync_rounds.py` 同步。
