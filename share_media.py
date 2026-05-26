"""
社交分享內容生成 — 照片濾鏡疊字、短視頻合成（ffmpeg 可選）
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import uuid
from datetime import datetime
from typing import Any
from urllib.request import urlretrieve

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from round_storage import BASE_DIR
from golf_utils import to_par_str

UPLOAD_ROOT = os.path.join(BASE_DIR, "static", "uploads", "share")
GENERATED_DIR = os.path.join(UPLOAD_ROOT, "generated")
FONT_DIR = os.path.join(BASE_DIR, "static", "fonts")
FONT_CANDIDATES = [
    os.path.join(FONT_DIR, "NotoSansTC-Regular.otf"),
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]
FONT_DOWNLOAD_URL = (
    "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/"
    "TraditionalChinese/NotoSansTC-Regular.otf"
)

PHOTO_STYLES = ("classic", "story", "minimal", "neon")
STYLE_SIZES = {
    "classic": (1080, 1080),
    "story": (1080, 1920),
    "minimal": (1200, 630),
    "neon": (1080, 1350),
}

MUSIC_TRACKS = [
    {
        "id": "fairway_morning",
        "name": "晨間球道 · 輕快律動",
        "file": "fairway_morning.mp3",
        "desc": "適合抖音開場、節奏明快",
    },
    {
        "id": "sunset_round",
        "name": "夕陽收桿 · 抒情氛圍",
        "file": "sunset_round.mp3",
        "desc": "適合小紅書敘事、溫暖感",
    },
    {
        "id": "clubhouse",
        "name": "會所慶祝 · 運動能量",
        "file": "clubhouse.mp3",
        "desc": "適合朋友圈高光集錦",
    },
]

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
ALLOWED_VIDEO_EXT = {".mp4", ".mov", ".webm", ".m4v"}
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_VIDEO_BYTES = 80 * 1024 * 1024


def _ensure_dirs():
    os.makedirs(GENERATED_DIR, exist_ok=True)
    os.makedirs(FONT_DIR, exist_ok=True)


def _resolve_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    _ensure_dirs()
    target = FONT_CANDIDATES[0]
    if not os.path.isfile(target):
        for path in FONT_CANDIDATES[1:]:
            if os.path.isfile(path):
                target = path
                break
        else:
            try:
                urlretrieve(FONT_DOWNLOAD_URL, target)
            except OSError:
                return ImageFont.load_default()
    try:
        return ImageFont.truetype(target, size)
    except OSError:
        return ImageFont.load_default()


def _safe_filename(name: str) -> str:
    base = os.path.basename(name or "upload")
    base = re.sub(r"[^\w.\-]", "_", base, flags=re.UNICODE)
    return base[:120] or "upload"


def build_share_meta(round_data: dict, player_name: str | None = None) -> dict[str, Any]:
    """從場次資料組出疊字用中繼資料"""
    players = sorted(round_data.get("players", []), key=lambda p: p["total"])
    if not players:
        return {}

    player = players[0]
    if player_name:
        for p in players:
            if p.get("name") == player_name:
                player = p
                break

    par_total = round_data.get("par_total") or 72
    to_par = player.get("to_par")
    if to_par is None:
        to_par = player["total"] - par_total

    highlight_holes: list[str] = []
    for hr in player.get("hole_results") or []:
        d = hr.get("diff", 99)
        if d <= 0:
            highlight_holes.append(f"第{hr['hole']}洞 {hr.get('name', 'Par')}")

    ranked = next(
        (i + 1 for i, p in enumerate(players) if p.get("name") == player.get("name")),
        1,
    )

    return {
        "round_id": round_data.get("id", ""),
        "course": round_data.get("course", "高爾夫球場"),
        "date": round_data.get("date", ""),
        "time": round_data.get("time", ""),
        "tee": round_data.get("tee", ""),
        "note": round_data.get("note", ""),
        "player_name": player.get("name", "球友"),
        "total": player["total"],
        "to_par": to_par,
        "to_par_label": to_par_str(to_par),
        "front9": player.get("front9"),
        "back9": player.get("back9"),
        "player_count": len(players),
        "rank": ranked,
        "highlights": highlight_holes[:4],
        "par_total": par_total,
    }


def list_music_tracks() -> list[dict]:
    audio_dir = os.path.join(BASE_DIR, "static", "audio")
    out = []
    for t in MUSIC_TRACKS:
        path = os.path.join(audio_dir, t["file"])
        out.append({**t, "available": os.path.isfile(path)})
    return out


def _music_path(track_id: str) -> str | None:
    for t in MUSIC_TRACKS:
        if t["id"] == track_id:
            path = os.path.join(BASE_DIR, "static", "audio", t["file"])
            if os.path.isfile(path):
                return path
    return None


def save_upload(file_storage, kind: str) -> tuple[str | None, str | None]:
    """儲存上傳檔，回傳 (磁碟路徑, 錯誤訊息)"""
    if not file_storage or not file_storage.filename:
        return None, "請選擇要上傳的檔案"

    _ensure_dirs()
    ext = os.path.splitext(file_storage.filename)[1].lower()
    allowed = ALLOWED_IMAGE_EXT if kind == "image" else ALLOWED_VIDEO_EXT
    if ext not in allowed:
        return None, f"不支援的格式 {ext}，請使用 {', '.join(sorted(allowed))}"

    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    limit = MAX_IMAGE_BYTES if kind == "image" else MAX_VIDEO_BYTES
    if size > limit:
        return None, f"檔案過大（上限 {limit // (1024 * 1024)}MB）"

    token = datetime.utcnow().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:8]
    dest = os.path.join(UPLOAD_ROOT, f"{token}_{_safe_filename(file_storage.filename)}")
    file_storage.save(dest)
    return dest, None


def _open_image(path: str) -> Image.Image:
    img = Image.open(path)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    elif img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (15, 40, 24))
        bg.paste(img, mask=img.split()[3])
        img = bg
    return img


def _apply_golf_filter(img: Image.Image) -> Image.Image:
    """專業高爾夫色調：略增飽和、對比，微綠暗部"""
    img = ImageEnhance.Contrast(img).enhance(1.08)
    img = ImageEnhance.Color(img).enhance(1.12)
    img = ImageEnhance.Brightness(img).enhance(1.03)
    img = ImageEnhance.Sharpness(img).enhance(1.06)
    # 輕微暗角
    w, h = img.size
    vignette = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(vignette)
    draw.ellipse((-w * 0.15, -h * 0.15, w * 1.15, h * 1.15), fill=210)
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=min(w, h) // 8))
    dark = Image.new("RGB", (w, h), (8, 35, 20))
    return Image.composite(img, dark, vignette)


def _fit_cover(img: Image.Image, tw: int, th: int) -> Image.Image:
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))


def _gradient_overlay(size: tuple[int, int], top_alpha: int = 0, bottom_alpha: int = 200) -> Image.Image:
    w, h = size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(h):
        t = y / max(h - 1, 1)
        if t < 0.35:
            a = int(top_alpha * (1 - t / 0.35))
        else:
            a = int(bottom_alpha * ((t - 0.35) / 0.65))
        draw.line([(0, y), (w, y)], fill=(10, 45, 28, min(255, a)))
    return overlay


def _draw_text_block(
    draw: ImageDraw.ImageDraw,
    meta: dict,
    w: int,
    h: int,
    style: str,
):
    f_title = _resolve_font(52 if style != "minimal" else 44)
    f_score = _resolve_font(120 if style == "neon" else 96)
    f_sub = _resolve_font(32)
    f_small = _resolve_font(24)

    course = meta.get("course", "")
    player = meta.get("player_name", "")
    total = str(meta.get("total", ""))
    to_par = meta.get("to_par_label", "")
    date_s = meta.get("date", "")
    count = meta.get("player_count", 0)
    tee = meta.get("tee", "")
    highlights = meta.get("highlights") or []

    gold = (234, 179, 8)
    white = (255, 255, 255)
    mint = (187, 247, 208)

    if style == "minimal":
        bar_h = int(h * 0.32)
        draw.rectangle((0, h - bar_h, w, h), fill=(22, 101, 52, 240))
        draw.text((48, h - bar_h + 36), course[:28], font=f_sub, fill=white)
        draw.text((48, h - bar_h + 80), f"{player}  ·  {date_s}  ·  {count} 位球友", font=f_small, fill=mint)
        tw = draw.textlength(total, font=f_score)
        draw.text((w - tw - 48, h - bar_h + 20), total, font=f_score, fill=gold)
        draw.text((w - 120, h - bar_h + 130), to_par, font=f_sub, fill=white)
        return

    y_base = h - 280 if style != "story" else h - 420
    draw.text((56, y_base - 120), "MAISON GOLF", font=f_small, fill=(*gold, 200) if hasattr(gold, "__iter__") else gold)
    draw.text((56, y_base - 70), course[:22] + ("…" if len(course) > 22 else ""), font=f_title, fill=white)

    line2 = f"{player}  ·  {date_s}"
    if tee:
        line2 += f"  ·  {tee}"
    draw.text((56, y_base - 10), line2, font=f_sub, fill=mint)
    draw.text((56, y_base + 44), f"{count} 位球友同組", font=f_small, fill=(200, 230, 210))

    draw.text((56, y_base + 100), total, font=f_score, fill=gold)
    draw.text((56 + draw.textlength(total, font=f_score) + 16, y_base + 150), to_par, font=f_title, fill=white)

    if highlights:
        hl = "亮點：" + " · ".join(highlights[:3])
        draw.text((56, y_base + 220), hl[:36] + ("…" if len(hl) > 36 else ""), font=f_small, fill=(180, 220, 190))

    if style == "neon":
        draw.rectangle((40, y_base - 140, w - 40, y_base + 280), outline=gold, width=3)
        draw.text((56, 56), "ROUND HIGHLIGHT", font=f_small, fill=gold)


def _render_style(img: Image.Image, meta: dict, style: str) -> Image.Image:
    tw, th = STYLE_SIZES[style]
    base = _fit_cover(img, tw, th)
    base = _apply_golf_filter(base)

    if style == "neon":
        tint = Image.new("RGB", (tw, th), (12, 55, 35))
        base = Image.blend(base, tint, 0.18)

    rgba = base.convert("RGBA")
    grad = _gradient_overlay((tw, th), bottom_alpha=220 if style != "minimal" else 0)
    rgba = Image.alpha_composite(rgba, grad)

    draw = ImageDraw.Draw(rgba)
    _draw_text_block(draw, meta, tw, th, style)

    if style == "classic":
        draw.ellipse((tw - 180, 40, tw - 40, 180), outline=(234, 179, 8), width=4)
        draw.text((tw - 155, 95), "⛳", font=_resolve_font(48), fill=(234, 179, 8))

    return rgba.convert("RGB")


def generate_photo_variants(
    source_path: str,
    meta: dict,
    styles: list[str] | None = None,
) -> tuple[list[dict], str | None]:
    """生成多風格分享圖，回傳 [{style, url, width, height}, ...]"""
    _ensure_dirs()
    try:
        img = _open_image(source_path)
    except OSError as e:
        return [], f"無法讀取圖片：{e}"

    use_styles = [s for s in (styles or PHOTO_STYLES) if s in STYLE_SIZES]
    if not use_styles:
        use_styles = list(PHOTO_STYLES)

    token = uuid.uuid4().hex[:10]
    results = []
    for style in use_styles:
        out_img = _render_style(img, meta, style)
        fname = f"{token}_{style}.jpg"
        out_path = os.path.join(GENERATED_DIR, fname)
        out_img.save(out_path, "JPEG", quality=92, optimize=True)
        tw, th = STYLE_SIZES[style]
        results.append({
            "style": style,
            "style_label": _style_label(style),
            "url": f"/static/uploads/share/generated/{fname}",
            "width": tw,
            "height": th,
        })
    return results, None


def _style_label(style: str) -> str:
    return {
        "classic": "經典方形 · 朋友圈",
        "story": "直式全屏 · 抖音/小紅書",
        "minimal": "橫幅精簡 · 微博/連結",
        "neon": "霓虹戰報 · 小紅書",
    }.get(style, style)


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def generate_share_video(
    source_path: str,
    meta: dict,
    music_id: str | None = None,
    duration_sec: int = 25,
) -> tuple[str | None, str | None]:
    """
    以 ffmpeg 合成短視頻：濾鏡、文字疊加、可選配樂。
    回傳 (輸出 URL, 錯誤)
    """
    if not _ffmpeg_available():
        return None, "伺服器尚未安裝 ffmpeg，視頻模式暫不可用（照片模式可正常使用）"

    _ensure_dirs()
    duration_sec = max(15, min(30, duration_sec))
    token = uuid.uuid4().hex[:10]
    out_name = f"{token}_clip.mp4"
    out_path = os.path.join(GENERATED_DIR, out_name)

    course = (meta.get("course") or "Golf")[:40].replace(":", "\\:").replace("'", "")
    player = (meta.get("player_name") or "")[:20].replace(":", "\\:")
    total = meta.get("total", "")
    to_par = (meta.get("to_par_label") or "").replace("+", "\\+")
    hl = meta.get("highlights") or []
    hl_txt = (hl[0] if hl else "Good round").replace(":", "\\:")[:30]

    # 文字疊加 + 飽和度；軌跡以動態提示文字模擬
    vf = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,"
        f"eq=saturation=1.15:brightness=0.04,"
        f"drawtext=text='Maison Golf':fontsize=36:fontcolor=0xEAB308:"
        f"x=60:y=80:box=1:boxcolor=0x0a2918@0.5:boxborderw=12,"
        f"drawtext=text='{course}':fontsize=42:fontcolor=white:x=60:y=140,"
        f"drawtext=text='{player}  {total} ({to_par})':fontsize=52:fontcolor=0xEAB308:"
        f"x=60:y=h-220,"
        f"drawtext=text='{hl_txt}':fontsize=34:fontcolor=0xBBF7D0:x=60:y=h-150,"
        f"drawtext=text='Ball flight ↗':fontsize=28:fontcolor=white@0.85:"
        f"x=w-280:y=h/2:enable='between(t,1,4)'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", source_path,
        "-t", str(duration_sec),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-an",
    ]

    music = _music_path(music_id) if music_id else None
    if music:
        cmd = [
            "ffmpeg", "-y",
            "-i", source_path,
            "-i", music,
            "-t", str(duration_sec),
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            "-map", "0:v:0",
            "-map", "1:a:0",
        ]

    cmd.append(out_path)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "視頻處理逾時，請縮短影片或稍後再試"
    except OSError as e:
        return None, str(e)

    if proc.returncode != 0 or not os.path.isfile(out_path):
        err = (proc.stderr or proc.stdout or "ffmpeg 失敗")[-400:]
        return None, f"視頻合成失敗：{err}"

    return f"/static/uploads/share/generated/{out_name}", None
