# 한글 → PDF 변환기

한글 문서(HWP, HWPX)를 PDF로 간편하게 변환하는 웹 애플리케이션입니다.

![Screenshot](https://img.shields.io/badge/Platform-Windows-blue) ![Python](https://img.shields.io/badge/Python-3.8+-green)

## ✨ 주요 기능

- 🔄 **드래그 앤 드롭** - 파일을 끌어서 놓기만 하면 변환
- 📁 **다중 파일 지원** - 여러 파일 동시 변환
- 📊 **실시간 진행 상태** - 변환 진행률 표시
- 📥 **개별/전체 다운로드** - PDF 개별 또는 ZIP으로 일괄 다운로드
- 🎨 **모던 UI** - 다크 테마의 프리미엄 디자인

## ⚠️ 요구 사항

> **중요:** 이 애플리케이션은 **한컴오피스 한글이 설치된 Windows**에서만 동작합니다.

- Windows 10/11
- Python 3.8 이상
- 한컴오피스 한글 (2020 이상 권장)

## 🚀 설치 및 실행

### 1. 저장소 클론

```bash
git clone https://github.com/YOUR_USERNAME/hancomtopdf.git
cd hancomtopdf
```

### 2. 가상 환경 생성 (선택 사항)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 서버 실행

```bash
python app.py
```

### 5. 브라우저에서 접속

```
http://localhost:5000
```

## 📁 프로젝트 구조

```
hancomtopdf/
├── app.py              # Flask 웹 서버
├── converter.py        # HWP → PDF 변환 모듈
├── requirements.txt    # Python 의존성
├── static/
│   ├── index.html      # 프론트엔드 HTML
│   ├── style.css       # 스타일시트
│   └── app.js          # 클라이언트 JavaScript
├── uploads/            # (자동 생성) 업로드 임시 폴더
└── outputs/            # (자동 생성) PDF 출력 폴더
```

## 🔧 설정

### 포트 변경

`app.py` 파일의 마지막 줄에서 포트를 변경할 수 있습니다:

```python
app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
```

### 다른 기기에서 접속

같은 네트워크의 다른 기기에서 접속하려면:

1. 방화벽에서 5000 포트 허용
2. `http://<서버IP>:5000`으로 접속

## 📝 라이선스

MIT License

## 🙏 감사의 말

- [pyhwpx](https://github.com/pyhwpx/pyhwpx) - 한컴오피스 자동화 라이브러리
- [Flask](https://flask.palletsprojects.com/) - Python 웹 프레임워크
