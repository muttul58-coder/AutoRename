"""
파일명 일괄 변경기 — 로컬 데스크탑 버전
pywebview + Python API로 파일시스템 직접 접근.
"""
import json
import os
import sys
import shutil
import struct
import subprocess
from datetime import datetime, timezone, timedelta

# Per-Monitor V2 DPI 인식 활성화 — WebView2 텍스트 선명도 개선
if sys.platform == "win32":
    try:
        import ctypes
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except Exception:
            pass

import webview
from webview.dom import DOMEventHandler

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


IMAGE_EXT = {".jpg", ".jpeg", ".tif", ".tiff", ".heic", ".heif",
             ".png", ".webp", ".cr2", ".nef", ".arw", ".dng"}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".3gp", ".3g2"}
EPOCH_1904 = 2082844800  # 1904-01-01 → 1970-01-01 (초)


# ---------- 파일 메타 ----------
def _parse_exif_dt(val):
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, str):
        # "YYYY:MM:DD HH:MM:SS"
        try:
            return datetime.strptime(val.strip(), "%Y:%m:%d %H:%M:%S").isoformat()
        except ValueError:
            return None
    return None


def get_image_exif_date(path):
    if not HAS_PIL:
        return None
    try:
        with Image.open(path) as img:
            exif = img._getexif()
            if not exif:
                return None
            wanted = ("DateTimeOriginal", "CreateDate", "DateTime")
            results = {}
            for tag, val in exif.items():
                name = TAGS.get(tag, "")
                if name in wanted:
                    parsed = _parse_exif_dt(val)
                    if parsed:
                        results[name] = parsed
            for key in wanted:
                if key in results:
                    return results[key]
            return None
    except Exception:
        return None


def get_video_creation_date(path):
    """MP4/MOV mvhd 박스의 creation_time 파싱."""
    try:
        size = os.path.getsize(path)
        chunks = []
        with open(path, "rb") as f:
            head = f.read(min(size, 1024 * 1024))
            chunks.append((0, head))
            if size > 1024 * 1024:
                f.seek(size - 1024 * 1024)
                tail = f.read()
                chunks.append((size - 1024 * 1024, tail))
        for _, buf in chunks:
            d = _parse_mvhd(buf)
            if d:
                return d.isoformat()
        return None
    except Exception:
        return None


def _find_box(buf, start, end, target):
    pos = start
    limit = min(end, len(buf))
    while pos + 8 <= limit:
        size = struct.unpack(">I", buf[pos:pos + 4])[0]
        box_type = buf[pos + 4:pos + 8].decode("ascii", errors="replace")
        header = 8
        if size == 1:
            if pos + 16 > len(buf):
                return None
            size = struct.unpack(">Q", buf[pos + 8:pos + 16])[0]
            header = 16
        elif size == 0:
            size = limit - pos
        if size < header:
            return None
        if box_type == target:
            return pos, header, size
        pos += size
    return None


def _parse_mvhd(buf):
    moov = _find_box(buf, 0, len(buf), "moov")
    if not moov:
        return None
    moov_pos, moov_hdr, moov_size = moov
    mvhd = _find_box(buf, moov_pos + moov_hdr, moov_pos + moov_size, "mvhd")
    if not mvhd:
        return None
    mvhd_pos, mvhd_hdr, _ = mvhd
    data = mvhd_pos + mvhd_hdr
    if data + 8 > len(buf):
        return None
    version = buf[data]
    ct_off = data + 4
    if version == 1:
        if ct_off + 8 > len(buf):
            return None
        ct = struct.unpack(">Q", buf[ct_off:ct_off + 8])[0]
    else:
        if ct_off + 4 > len(buf):
            return None
        ct = struct.unpack(">I", buf[ct_off:ct_off + 4])[0]
    if not ct:
        return None
    ts = ct - EPOCH_1904
    try:
        d = datetime.fromtimestamp(ts)
        if 1980 <= d.year <= 2100:
            return d
    except (OSError, OverflowError, ValueError):
        pass
    return None


# ---------- API ----------
class API:
    def pick_folder(self):
        """네이티브 폴더 선택 대화상자 → 절대 경로 반환."""
        window = webview.windows[0]
        result = window.create_file_dialog(webview.FOLDER_DIALOG)
        if not result:
            return None
        return result[0]

    def pick_dest_folder(self):
        return self.pick_folder()

    def use_folder(self, path):
        """드래그앤드롭으로 받은 경로가 실제 폴더인지 검증 → 절대 경로 반환."""
        if not path:
            return None
        try:
            abs_path = os.path.abspath(path)
            if os.path.isdir(abs_path):
                return abs_path
            # 파일이 드롭된 경우 → 부모 폴더 사용
            if os.path.isfile(abs_path):
                return os.path.dirname(abs_path)
        except (OSError, ValueError):
            pass
        return None

    def list_dir(self, path):
        """폴더 내용 한 단계만 나열."""
        out = []
        try:
            with os.scandir(path) as it:
                for entry in it:
                    is_dir = entry.is_dir(follow_symlinks=False)
                    item = {
                        "name": entry.name,
                        "path": entry.path,
                        "is_dir": is_dir,
                    }
                    if not is_dir:
                        try:
                            item["mtime"] = entry.stat().st_mtime
                            item["size"] = entry.stat().st_size
                        except OSError:
                            item["mtime"] = None
                            item["size"] = 0
                    out.append(item)
        except OSError as e:
            return {"error": str(e)}
        return out

    def get_file_date(self, path):
        """확장자에 맞춰 EXIF/영상 메타 → ISO 문자열. 실패하면 mtime."""
        ext = os.path.splitext(path)[1].lower()
        if ext in IMAGE_EXT:
            d = get_image_exif_date(path)
            if d:
                return {"date": d, "source": "exif"}
        elif ext in VIDEO_EXT:
            d = get_video_creation_date(path)
            if d:
                return {"date": d, "source": "video"}
        try:
            mt = os.path.getmtime(path)
            return {"date": datetime.fromtimestamp(mt).isoformat(), "source": "mtime"}
        except OSError:
            return {"date": None, "source": None}

    def rename(self, src, dst):
        try:
            os.rename(src, dst)
            return {"ok": True}
        except OSError as e:
            return {"ok": False, "error": str(e)}

    def copy_file(self, src, dst):
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            return {"ok": True}
        except OSError as e:
            return {"ok": False, "error": str(e)}

    def make_dir(self, path):
        try:
            os.makedirs(path, exist_ok=True)
            return {"ok": True}
        except OSError as e:
            return {"ok": False, "error": str(e)}

    def path_exists(self, path):
        return os.path.exists(path)

    def join(self, *parts):
        return os.path.join(*parts)

    def open_folder(self, path):
        try:
            if not os.path.exists(path):
                return {"ok": False, "error": "경로가 존재하지 않습니다."}
            if sys.platform == "win32":
                os.startfile(path)  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
            return {"ok": True}
        except OSError as e:
            return {"ok": False, "error": str(e)}


def _resource_path(name):
    """PyInstaller로 빌드된 경우 _MEIPASS 임시 폴더를, 아니면 스크립트 폴더를 사용."""
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, name)


def _on_dropzone_drop(window, event):
    files = event.get("dataTransfer", {}).get("files", []) or []
    for f in files:
        path = f.get("pywebviewFullPath")
        if not path:
            continue
        try:
            if os.path.isdir(path):
                folder = path
            elif os.path.isfile(path):
                folder = os.path.dirname(path)
            else:
                continue
            window.evaluate_js(f"useFolderPath({json.dumps(folder)})")
            return
        except OSError:
            continue


def _wire_drag_drop(window):
    def attach():
        dropzone = window.dom.get_element("#dropzone")
        if dropzone is None:
            return
        # dragover는 기본 동작을 막아야 drop이 트리거됨
        dropzone.events.dragover += DOMEventHandler(lambda e: None, prevent_default=True)
        dropzone.events.drop += DOMEventHandler(
            lambda e: _on_dropzone_drop(window, e), prevent_default=True
        )
    window.events.loaded += attach


def main():
    if not HAS_PIL:
        print("[경고] Pillow가 설치되어 있지 않아 EXIF 추출이 동작하지 않습니다.")
        print("       pip install Pillow")
    html_path = _resource_path("index.html")
    window = webview.create_window(
        "📁 파일명 일괄 변경기 (로컬)",
        html_path,
        js_api=API(),
        width=1180,
        height=860,
        min_size=(900, 600),
    )
    _wire_drag_drop(window)
    webview.start()


if __name__ == "__main__":
    main()
