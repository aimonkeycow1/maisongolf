"""
記分卡 Par 自動辨識（Grok Vision / xAI）。

流程：上傳紙本記分卡照片 → Pillow 轉正/增強/壓縮 → Grok Vision 讀出 18 洞 Par。
環境變數：
  - XAI_API_KEY / GROK_API_KEY：xAI 金鑰（沿用 AI 教練同一把）
  - GROK_VISION_MODEL：視覺模型（預設 grok-2-vision-1212）
  - OCR_MOCK：設為 1/true 時，無金鑰也回傳一組模擬 Par，方便本機測試流程

回傳結構：
  ({"pars":[...18], "confidence":0~1, "par_total":int, "warnings":[...]}, None)
  或 (None, error_message)。無金鑰或無法解析時回 error，前端自動回退到模板。
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import urllib.error
import urllib.request

XAI_CHAT_URL = "https://api.x.ai/v1/chat/completions"
VISION_MODEL = os.environ.get("GROK_VISION_MODEL", "grok-2-vision-1212")

HOLES = 18
MAX_EDGE = 2000  # 壓縮後長邊像素：密集記分卡需要較高解析度才看得清小數字
PAR_MIN, PAR_MAX = 3, 6
TOTAL_MIN, TOTAL_MAX = 68, 74  # 常見 18 洞總 Par 範圍，用於合理性提醒

_SYSTEM_PROMPT = """你是高爾夫記分卡判讀助手。使用者上傳一張紙本記分卡照片，你要讀出 18 個洞的「Par（標準桿）」。

判讀步驟：
1. 找出標記為「Par」「PAR」「標準桿」的那一列（row）。記分卡通常分前九 (OUT / 1-9) 與後九 (IN / 10-18)，可能在同一列分兩段，或分成上下兩塊。
2. 依洞號 1→18 的順序，讀出每一洞對應的 Par。
3. 若記分卡只有 9 洞，無法湊滿 18 洞時，confidence 給低分並盡量填合理值。

務必避免誤判：
- Par 值很小，幾乎都是 3、4、5（偶爾 6）。
- 「碼數 / Yardage / 距離」是三位數（如 380、512），不是 Par。
- 「差點 / HCP / Handicap / Index」是 1~18 的不重複排序，不是 Par。
- 「桿數 / Score」是球員實際成績，不是 Par。
- 「Total / OUT / IN 合計」是加總欄位，不要當成某一洞。

自我檢查：前九與後九各自 Par 合計多為 34~37；全 18 洞總和多為 70~73。讀完用這個檢查，明顯不合理就重看一次。

輸出規定（非常重要）：
- 只輸出 JSON，不要任何說明文字、不要 markdown 圍欄。
- 格式固定：{"pars":[p1,...,p18],"confidence":0.0~1.0}
- pars 必須恰好 18 個整數。
- confidence 反映你的把握程度：清楚可辨給 0.85+，部分靠推估給 0.4~0.7，幾乎看不清給 <0.4。"""

_USER_TEXT = "請讀出這張記分卡 18 洞的 Par，依洞號 1 到 18 排序，只回 JSON。"


# ─────────────────────────── 影像前處理 ───────────────────────────
def _prep_image_b64(image_bytes: bytes) -> str | None:
    """轉正(EXIF) → 灰階 → 自動對比 → 等比縮放 → JPEG base64。Pillow 不可用時退回原圖。"""
    try:
        from PIL import Image, ImageOps

        img = Image.open(io.BytesIO(image_bytes))
        # 1) 依 EXIF 方向轉正（手機直拍最常見的錯誤來源）
        img = ImageOps.exif_transpose(img)
        # 2) 灰階 + 自動對比，讓印刷數字更清楚
        img = ImageOps.grayscale(img)
        img = ImageOps.autocontrast(img, cutoff=1)
        # 3) 等比縮放長邊到 MAX_EDGE（過小的圖不放大，避免糊上加糊）
        w, h = img.size
        scale = min(1.0, MAX_EDGE / float(max(w, h)))
        if scale < 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        # 灰階轉回 RGB 存 JPEG（相容性最佳）
        img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        try:
            return base64.b64encode(image_bytes).decode("ascii")
        except Exception:
            return None


# ─────────────────────────── 解析 ───────────────────────────
def _extract_json(text: str) -> dict | list | None:
    if not text:
        return None
    s = text.strip()
    # 去除 ```json ... ``` 圍欄
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s).strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # 嘗試抓出物件 {...}
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    # 嘗試抓出純陣列 [...]
    m = re.search(r"\[.*\]", s, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _validate_pars(parsed) -> tuple[dict | None, str | None]:
    """寬鬆驗證：恰好 18 個數字才接受；超出 3~6 的值夾回範圍並記 warning，不整批失敗。"""
    if isinstance(parsed, list):
        raw = parsed
        conf_raw = None
    elif isinstance(parsed, dict):
        raw = parsed.get("pars")
        conf_raw = parsed.get("confidence")
    else:
        return None, "辨識結果格式錯誤"

    if not isinstance(raw, list) or len(raw) != HOLES:
        return None, "未能讀出完整 18 洞 Par"

    warnings: list[str] = []
    clamped = 0
    out: list[int] = []
    for p in raw:
        try:
            v = int(round(float(p)))
        except (TypeError, ValueError):
            return None, "Par 數值格式錯誤"
        if v < PAR_MIN:
            v = PAR_MIN
            clamped += 1
        elif v > PAR_MAX:
            v = PAR_MAX
            clamped += 1
        out.append(v)

    try:
        conf = float(conf_raw) if conf_raw is not None else 0.5
    except (TypeError, ValueError):
        conf = 0.5
    conf = max(0.0, min(1.0, conf))

    par_total = sum(out)
    if clamped:
        conf = min(conf, 0.5)
        warnings.append("有洞的 Par 看不太清楚，已先給一個合理值，請仔細核對")
    if not (TOTAL_MIN <= par_total <= TOTAL_MAX):
        conf = min(conf, 0.55)
        warnings.append(f"讀到的總 Par 為 {par_total}，不在常見範圍，請特別核對")

    return {
        "pars": out,
        "confidence": round(conf, 2),
        "par_total": par_total,
        "warnings": warnings,
    }, None


# ─────────────────────────── 對外主函式 ───────────────────────────
def _mock_result() -> dict:
    return {
        "pars": [4, 4, 3, 5, 4, 4, 3, 4, 5, 4, 3, 4, 5, 4, 4, 3, 4, 5],
        "confidence": 0.42,
        "par_total": 72,
        "warnings": ["（本機測試模擬資料，非真實辨識）請核對每洞 Par"],
    }


def _truthy(val: str | None) -> bool:
    return (val or "").strip().lower() in ("1", "true", "yes", "on")


def _mock_enabled() -> bool:
    """OCR_MOCK 預設為 True（測試版）。設為 false/0/no 才會嘗試真實辨識。"""
    return _truthy(os.environ.get("OCR_MOCK", "true"))


def describe_mode() -> str:
    """供啟動 log 顯示目前拍照讀 Par 的模式。"""
    api_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if _mock_enabled():
        return "MOCK（模擬資料，測試用；設 OCR_MOCK=false 並填 XAI_API_KEY 可切真實）"
    if api_key:
        return f"REAL（{VISION_MODEL}）"
    return "停用（未設 XAI_API_KEY，會提示用戶改用手動模板）"


def _call_vision(api_key: str, b64: str) -> tuple[str | None, str | None]:
    """呼叫一次 Vision API，回 (content, error)。"""
    payload = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _USER_TEXT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
        "temperature": 0.0,
        "max_tokens": 400,
    }
    req = urllib.request.Request(
        XAI_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        return None, f"辨識服務錯誤（{e.code}），請改用模板"
    except (urllib.error.URLError, TimeoutError):
        return None, "辨識服務連線逾時，請改用模板"
    except (KeyError, json.JSONDecodeError):
        return None, "辨識結果無法解析，請改用模板"


def read_scorecard_pars(image_bytes: bytes) -> tuple[dict | None, str | None]:
    """回傳 ({"pars","confidence","par_total","warnings"}, None) 或 (None, error)。"""
    api_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")

    # OCR_MOCK 預設開啟（測試版）：一律回模擬資料，方便手機直接體驗流程。
    # 要切換真實辨識：設 OCR_MOCK=false 並提供 XAI_API_KEY。
    if _mock_enabled():
        return _mock_result(), None
    if not api_key:
        return None, "尚未設定辨識服務（XAI_API_KEY），請改用手動模板"
    if not image_bytes:
        return None, "沒有收到圖片"

    b64 = _prep_image_b64(image_bytes)
    if not b64:
        return None, "圖片處理失敗，請改用手動模板"

    # 最多嘗試兩次：第一次失敗（解析不出 18 洞）時再讀一次
    last_err = None
    for attempt in range(2):
        content, err = _call_vision(api_key, b64)
        if err:
            last_err = err
            # 連線/服務類錯誤不重試
            break
        result, perr = _validate_pars(_extract_json(content or ""))
        if result:
            return result, None
        last_err = perr or "辨識結果無法解析，請改用模板"

    return None, last_err or "辨識失敗，請改用手動模板"
