"""
本機錄分後，把 rounds.json 同步到雲端網站。

用法（第一次先設定網址與密鑰）：
  export DEPLOY_URL="https://你的網址.onrender.com"
  export SYNC_KEY="在 Render 後台看到的 SYNC_SECRET"

  python3 sync_rounds.py
"""

import json
import os
import sys
import urllib.error
import urllib.request

from round_storage import load_rounds


def main():
    url = os.environ.get("DEPLOY_URL", "").rstrip("/")
    key = os.environ.get("SYNC_KEY", "")

    if not url or not key:
        print("請先設定環境變數：")
        print('  export DEPLOY_URL="https://xxx.onrender.com"')
        print('  export SYNC_KEY="你的 SYNC_SECRET"')
        sys.exit(1)

    data = load_rounds()
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{url}/admin/sync",
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Sync-Key": key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
        print(f"✅ 同步成功！共 {result.get('rounds', '?')} 場")
        print(f"   網址：{url}")
    except urllib.error.HTTPError as e:
        print(f"❌ 同步失敗 HTTP {e.code}")
        print(e.read().decode())
        sys.exit(1)


if __name__ == "__main__":
    main()
