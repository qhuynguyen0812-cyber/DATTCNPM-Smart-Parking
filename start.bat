@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo ==========================================================
echo    ITS Parking - He thong nhan dien bien so xe may
echo ==========================================================
echo.

REM --- Tim Python ---
set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    where python >nul 2>nul
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    echo [!] Khong tim thay Python. Cai Python 3.11+ truoc.
    pause
    exit /b 1
)

REM --- Kiem tra thu vien ---
%PY% -c "import fastapi, uvicorn" >nul 2>nul
if errorlevel 1 (
    echo [*] Lan dau chay - dang cai thu vien...
    %PY% -m pip install -r requirements_web.txt
    if errorlevel 1 (
        echo [!] Cai thu vien that bai. Xem loi phia tren.
        pause
        exit /b 1
    )
)

REM --- Seed tai khoan demo neu chua co ---
%PY% -c "import sys; sys.path.insert(0,'.'); from scripts.seed_demo_users import seed_demo_users; seed_demo_users()" >nul 2>nul

echo [*] Khoi dong ung dung web...
echo [*] Mo trinh duyet: http://localhost:8000
echo [*] Tai khoan demo: admin / ItsDemo@2026A
echo.
start "" http://localhost:8000
%PY% -m uvicorn api.main:app --host 0.0.0.0 --port 8000

pause
endlocal
