@echo off
chcp 65001 > nul
title 한글 → PDF 변환기

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║           한글 → PDF 변환기                              ║
echo ║           HWP to PDF Converter                           ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

:: 현재 스크립트 디렉토리로 이동
cd /d "%~dp0"

:: Python 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo Python 3.8 이상을 설치해주세요: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 가상환경 확인 및 생성
if not exist "venv" (
    echo [설정] 가상환경을 생성하고 있습니다...
    python -m venv venv
    if errorlevel 1 (
        echo [오류] 가상환경 생성에 실패했습니다.
        pause
        exit /b 1
    )
)

:: 가상환경 활성화
call venv\Scripts\activate.bat

:: 의존성 설치 확인
if not exist "venv\installed.flag" (
    echo [설정] 필요한 패키지를 설치하고 있습니다...
    pip install -r requirements.txt -q
    if errorlevel 1 (
        echo [오류] 패키지 설치에 실패했습니다.
        pause
        exit /b 1
    )
    echo. > venv\installed.flag
    echo [완료] 패키지 설치가 완료되었습니다.
)

echo.
echo [시작] 서버를 시작합니다...
echo [정보] 브라우저가 자동으로 열립니다.
echo [정보] 종료하려면 이 창을 닫거나 Ctrl+C를 누르세요.
echo.

:: 2초 후 브라우저 열기 (백그라운드)
start /b cmd /c "timeout /t 2 /nobreak > nul && start http://localhost:5000"

:: Flask 서버 실행
python app.py
