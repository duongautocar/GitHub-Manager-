@echo off
title GitHub Manager - Cài đặt và chạy
color 0A

echo ===================================================
echo   GitHub Manager - Cài đặt và chạy ứng dụng
echo ===================================================
echo.
echo [1/4] Kiem tra Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python chua duoc cai dat!
    echo     Tai Python tai: https://www.python.org/downloads/
    echo     Nho tick chon "Add Python to PATH" khi cai dat.
    pause
    exit /b
)
echo [OK] Python da duoc cai dat.
echo.

echo [2/4] Kiem tra Git...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Git chua duoc cai dat!
    echo     Tai Git tai: https://git-scm.com/download/win
    pause
    exit /b
)
echo [OK] Git da duoc cai dat.
echo.

echo [3/4] Dang cai dat thu vien Python...
echo (Dang dung: python -m pip install -r requirements.txt)
python -m pip install -r requirements.txt
echo.
if %errorlevel% neq 0 (
    echo [!] Loi cai dat thu vien. Thu cai bang tay:
    echo     python -m pip install customtkinter PyGithub Pillow
    pause
    exit /b
)
echo [OK] Da cai dat thu vien thanh cong.
echo.

echo [4/4] Dang chay ung dung...
echo.
echo ===================================================
echo   Ung dung sap duoc mo. Vui long cho...
echo ===================================================
echo.
python main_app.py

pause