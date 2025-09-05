# Auto Scroll Browser

웹페이지를 자동으로 스크롤하면서 `page0`, `page1` 형식의 이미지를 다운로드하고 PDF로 변환하는 도구입니다.

## 설치

```bash
pip install -r requirements.txt
```

## 사용법

### 1. 명령행에서 실행

```bash
# 대화식 모드
python auto_scroll_browser.py

# 직접 URL 지정
python auto_scroll_browser.py https://example.com --download-images
```

### 2. 다른 Python 프로그램에서 임포트

```python
from auto_scroll_browser import scroll_and_download_from_url, auto_scroll_page

# 간단한 이미지 다운로드 및 PDF 생성
result = scroll_and_download_from_url("https://example.com")

if result['success']:
    print(f"PDF 생성 완료: {result['pdf_path']}")
    print(f"이미지 {result['downloaded_count']}개 다운로드")
```

## API 함수

### `scroll_and_download_from_url(url, scroll_delay=2, headless=True, keep_browser_open=False)`

웹페이지를 스크롤하면서 이미지를 다운로드하고 PDF를 생성합니다.

**매개변수:**
- `url` (str): 처리할 URL
- `scroll_delay` (float): 스크롤 간격 (초)
- `headless` (bool): 백그라운드에서 실행 여부
- `keep_browser_open` (bool): 브라우저를 열어둘지 여부

**반환값:**
```python
{
    'success': bool,           # 성공 여부
    'images_dir': str,         # 이미지 저장 폴더
    'pdf_path': str,          # 생성된 PDF 경로
    'downloaded_count': int,   # 다운로드된 이미지 수
    'error': str              # 오류 메시지 (실패시)
}
```

### `auto_scroll_page(url, scroll_delay=2, download_images=False, headless=False)`

웹페이지를 자동 스크롤합니다. 옵션으로 이미지 다운로드 가능.

**매개변수:**
- `url` (str): 처리할 URL
- `scroll_delay` (float): 스크롤 간격 (초)
- `download_images` (bool): 이미지 다운로드 여부
- `headless` (bool): 백그라운드에서 실행 여부

## 사용 예시

### 예시 1: 기본 사용법

```python
from auto_scroll_browser import scroll_and_download_from_url

# 웹페이지에서 이미지 다운로드 및 PDF 생성
result = scroll_and_download_from_url("https://example.com")

if result['success']:
    print(f"성공! {result['downloaded_count']}개 이미지 다운로드")
    print(f"PDF: {result['pdf_path']}")
else:
    print(f"실패: {result['error']}")
```

### 예시 2: 여러 URL 일괄 처리

```python
from auto_scroll_browser import scroll_and_download_from_url

urls = [
    "https://site1.com",
    "https://site2.com", 
    "https://site3.com"
]

for url in urls:
    result = scroll_and_download_from_url(url, headless=True)
    if result['success']:
        print(f"{url}: {result['downloaded_count']}개 이미지 처리 완료")
```

### 예시 3: 브라우저 표시하며 실행

```python
from auto_scroll_browser import scroll_and_download_from_url

# 브라우저를 보면서 실행
result = scroll_and_download_from_url(
    "https://example.com",
    headless=False,
    scroll_delay=1.5
)
```

## 파일 구조

```
downloaded_images/
└── 20250905_143022_a1b2c3d4/    # 날짜_시간_해시
    ├── page0.jpg
    ├── page1.png
    └── page2.jpg

downloaded/
└── 20250905_143022_a1b2c3d4.pdf
```

## 특징

- **iframe 및 특정 div 지원**: `id="contents"`인 div 우선 스크롤
- **빠른 다운로드**: 멀티스레딩으로 동시 다운로드
- **자동 PDF 생성**: 페이지 순서대로 정렬하여 PDF 생성
- **충돌 방지**: 타임스탬프 + 해시로 고유한 파일명
- **배치 처리**: 여러 URL을 순차적으로 처리 가능

## 요구사항

- Python 3.7+
- Chrome 브라우저
- ChromeDriver (selenium이 자동 관리)

## 라이선스

MIT License# ReadOnlyPdf_Downloader
