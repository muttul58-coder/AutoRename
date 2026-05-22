# 파일명 일괄 변경기 — 로컬 버전

웹 버전과 동일한 UI를 데스크탑 창에서 실행합니다. 브라우저 보안 제약이 없으므로 다음이 가능합니다.

- **선택한 폴더의 전체 경로 표시** (예: `C:\Users\user\Pictures\행사`)
- **작업 완료 후 결과 폴더를 탐색기로 바로 열기**
- 네이티브 폴더 선택 대화상자

## 요구사항
- Python 3.9 이상 (Windows: PATH 등록 필수)
- 최초 실행 시 자동으로 `.venv`를 만들고 의존성 설치

## 실행
```
run.bat 더블클릭
```

또는 수동:
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 의존성
- `pywebview` — 네이티브 창 + JS↔Python 브리지
- `Pillow` — JPEG/HEIC EXIF 파싱

## 웹 버전과의 차이

| | 웹 (GitHub Pages) | 로컬 (이 폴더) |
|--|--|--|
| 전체 경로 표시 | ❌ 폴더 이름만 | ✅ |
| 결과 폴더 열기 | ❌ | ✅ |
| 설치 | 필요 없음 | Python + pywebview |
| 파일 처리 | 브라우저 FileSystem API | Python `os`/`shutil` |
| EXIF 파싱 | exifr (JS) | Pillow (Python) |

기능(자동/수동 규칙, 미리보기, 덮어쓰기/복사)은 동일합니다.

## 단일 실행파일(.exe) 빌드 — Python 없는 PC에 배포용

```
build.bat 더블클릭
```

- PyInstaller가 Python 런타임·의존성·HTML을 하나의 `.exe`로 묶습니다.
- 결과물: `dist\파일명변경기.exe` (약 30~50MB)
- 이 `.exe` 파일만 다른 PC로 복사하면 **Python 설치 없이** 실행됩니다.
- 빌드 자체에는 Python이 필요합니다 (배포 대상 PC에는 불필요).

> ⚠ 일부 백신 프로그램이 PyInstaller로 만든 .exe를 오탐할 수 있습니다. 신뢰할 수 있는 빌드 환경에서 직접 빌드하시는 것을 권장합니다.

