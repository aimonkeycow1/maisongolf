"""會員頭像：Cloudinary CDN（正式環境）或本機 static（開發備援）"""

from __future__ import annotations

import os
import uuid
from io import BytesIO
from typing import Any
from urllib.parse import urlparse, urlunparse

from PIL import Image
from werkzeug.utils import secure_filename

from round_storage import BASE_DIR

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
MIME_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}
MAX_BYTES = 2 * 1024 * 1024
AVATAR_SIZE = (256, 256)
CLOUDINARY_FOLDER = "maisongolf/avatars"

_DATA_ROOT = (os.environ.get("INSTANCE_DATA_DIR") or "").strip()
if _DATA_ROOT:
    AVATAR_DIR = os.path.join(_DATA_ROOT, "avatars")
else:
    AVATAR_DIR = os.path.join(BASE_DIR, "static", "uploads", "avatars")


def cloudinary_configured() -> bool:
    return bool(
        (os.environ.get("CLOUDINARY_CLOUD_NAME") or "").strip()
        and (os.environ.get("CLOUDINARY_API_KEY") or "").strip()
        and (os.environ.get("CLOUDINARY_API_SECRET") or "").strip()
    )


def _configure_cloudinary() -> None:
    import cloudinary

    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"].strip(),
        api_key=os.environ["CLOUDINARY_API_KEY"].strip(),
        api_secret=os.environ["CLOUDINARY_API_SECRET"].strip(),
        secure=True,
    )


def cloudinary_public_id_for_user(user_id: int) -> str:
    return f"{CLOUDINARY_FOLDER}/user_{int(user_id)}"


def ensure_avatar_upload_dir() -> None:
    """本機備援目錄（未設定 Cloudinary 時使用）。"""
    if cloudinary_configured():
        return
    os.makedirs(AVATAR_DIR, exist_ok=True)
    legacy = os.path.join(BASE_DIR, "static", "uploads", "avatars")
    if legacy != AVATAR_DIR:
        os.makedirs(legacy, exist_ok=True)


def avatar_relative_path(user_id: int) -> str:
    return f"uploads/avatars/user_{int(user_id)}.jpg"


def avatar_disk_path(user_id: int) -> str:
    return os.path.join(AVATAR_DIR, f"user_{int(user_id)}.jpg")


def avatar_exists_on_disk(user_id: int) -> bool:
    return os.path.isfile(avatar_disk_path(user_id))


def user_has_avatar(user) -> bool:
    if not user:
        return False
    if getattr(user, "avatar_url", None):
        return True
    path = getattr(user, "avatar_path", None)
    if path and str(path).startswith("http"):
        return True
    return bool(path)


def resolve_avatar_url(user, *, external: bool = False) -> str | None:
    """
    供模板 <img src> 使用。
    external=True 時回傳完整 URL（Cloudinary 或本機需 request 時由呼叫端處理）。
    """
    if not user or not user_has_avatar(user):
        return None

    rev = int(getattr(user, "avatar_revision", None) or 0)
    url = (getattr(user, "avatar_url", None) or "").strip()
    if not url:
        path = (getattr(user, "avatar_path", None) or "").strip()
        if path.startswith("http://") or path.startswith("https://"):
            url = path

    if url:
        return _append_cache_bust(url, rev)

    path = (getattr(user, "avatar_path", None) or "").strip()
    if not path:
        return None

    if external:
        return None
    try:
        from flask import url_for

        return url_for("auth.avatar_image", user_id=user.id, v=rev)
    except Exception:
        return None


def _append_cache_bust(url: str, revision: int) -> str:
    if revision <= 0:
        return url
    parsed = urlparse(url)
    q = parsed.query
    sep = "&" if q else ""
    new_q = f"{q}{sep}v={revision}" if q else f"v={revision}"
    return urlunparse(parsed._replace(query=new_q))


def _guess_ext(filename: str, content_type: str | None, raw: bytes) -> str | None:
    name = secure_filename(filename or "") or ""
    ext = os.path.splitext(name)[1].lower()
    if ext in ALLOWED_EXT:
        return ext
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct in MIME_EXT:
        return MIME_EXT[ct]
    if raw[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return ".webp"
    if len(raw) >= 12 and raw[4:8] in (b"ftyp",):
        brand = raw[8:12]
        if brand in (b"heic", b"heix", b"hevc", b"mif1"):
            return ".heic"
    return None


def _open_image(raw: bytes, ext: str) -> Image.Image:
    buf = BytesIO(raw)
    try:
        img = Image.open(buf)
        img.load()
        return img
    except Exception as exc:
        if ext in (".heic", ".heif"):
            raise ValueError(
                "iPhone HEIC 格式目前無法處理，請在相簿中「分享→儲存圖片」"
                " 或將相機格式改為「最相容」後再試"
            ) from exc
        raise ValueError("無法讀取圖片，請換一張 JPG 或 PNG 試試") from exc


def _process_to_jpeg_bytes(raw: bytes, ext: str) -> bytes:
    img = _open_image(raw, ext)
    img = img.convert("RGB")
    img.thumbnail(AVATAR_SIZE, Image.Resampling.LANCZOS)
    w, h = img.size
    if w != h:
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))
        img = img.resize(AVATAR_SIZE, Image.Resampling.LANCZOS)
    out = BytesIO()
    img.save(out, format="JPEG", quality=88, optimize=True)
    return out.getvalue()


def _upload_cloudinary(user_id: int, jpeg_bytes: bytes) -> dict[str, str]:
    import cloudinary.uploader

    _configure_cloudinary()
    public_id = cloudinary_public_id_for_user(user_id)
    result = cloudinary.uploader.upload(
        jpeg_bytes,
        public_id=public_id,
        overwrite=True,
        resource_type="image",
        format="jpg",
    )
    secure_url = result.get("secure_url") or result.get("url")
    if not secure_url:
        raise RuntimeError("Cloudinary 未回傳圖片網址")
    return {
        "avatar_url": secure_url,
        "avatar_public_id": result.get("public_id") or public_id,
        "avatar_path": None,
    }


def _save_local_disk(user_id: int, jpeg_bytes: bytes) -> dict[str, str]:
    ensure_avatar_upload_dir()
    dest = avatar_disk_path(user_id)
    tmp = dest + f".{uuid.uuid4().hex}.tmp"
    with open(tmp, "wb") as f:
        f.write(jpeg_bytes)
    os.replace(tmp, dest)
    return {
        "avatar_url": None,
        "avatar_public_id": None,
        "avatar_path": avatar_relative_path(user_id),
    }


def save_user_avatar(user_id: int, file_storage) -> tuple[dict[str, Any] | None, str | None]:
    """
    儲存頭像，回傳 (欄位更新 dict, 錯誤訊息)。
    dict 含 avatar_url, avatar_public_id, avatar_path。
    """
    if not file_storage:
        return None, "請選擇頭像圖片"

    raw = file_storage.read()
    if not raw:
        return None, "請選擇頭像圖片"
    if len(raw) > MAX_BYTES:
        return None, "頭像檔案不可超過 2MB"

    ext = _guess_ext(getattr(file_storage, "filename", "") or "", file_storage.content_type, raw)
    if not ext:
        return None, "僅支援 JPG、PNG、WEBP（iPhone 請先儲存為 JPG 再上傳）"

    try:
        jpeg_bytes = _process_to_jpeg_bytes(raw, ext)
        if cloudinary_configured():
            meta = _upload_cloudinary(user_id, jpeg_bytes)
        else:
            meta = _save_local_disk(user_id, jpeg_bytes)
        return meta, None
    except ValueError as e:
        return None, str(e)
    except Exception as e:
        if cloudinary_configured():
            return None, f"頭像上傳失敗：{e}"
        return None, "伺服器無法寫入頭像檔，請稍後再試或聯絡管理員"


def remove_user_avatar(
    user_id: int,
    *,
    avatar_public_id: str | None = None,
    current_path: str | None = None,
) -> None:
    pid = (avatar_public_id or "").strip()
    if cloudinary_configured() and pid:
        try:
            import cloudinary.uploader

            _configure_cloudinary()
            cloudinary.uploader.destroy(pid, resource_type="image")
        except Exception:
            pass
    path = avatar_disk_path(user_id)
    if os.path.isfile(path):
        os.remove(path)
    if current_path and not str(current_path).startswith("http"):
        legacy = os.path.join(BASE_DIR, "static", current_path)
        if os.path.isfile(legacy):
            os.remove(legacy)


def migrate_local_avatars_to_cloudinary() -> int:
    """一次性：將本機 static 頭像上傳至 Cloudinary（需已設定環境變數）。"""
    if not cloudinary_configured():
        return 0
    try:
        from models import User
    except Exception:
        return 0

    migrated = 0
    for u in User.query.filter(User.avatar_path.isnot(None), User.avatar_url.is_(None)).all():
        path = (u.avatar_path or "").strip()
        if not path or path.startswith("http"):
            continue
        disk = os.path.join(BASE_DIR, "static", path)
        if not os.path.isfile(disk):
            disk = avatar_disk_path(u.id)
        if not os.path.isfile(disk):
            continue
        try:
            with open(disk, "rb") as f:
                raw = f.read()
            meta = _upload_cloudinary(u.id, raw)
            u.avatar_url = meta["avatar_url"]
            u.avatar_public_id = meta["avatar_public_id"]
            u.avatar_path = None
            u.avatar_revision = (u.avatar_revision or 0) + 1
            migrated += 1
        except Exception as exc:
            print(f"⚠️ 頭像遷移 user {u.id} 失敗: {exc}")
    if migrated:
        from models import db

        db.session.commit()
    return migrated
