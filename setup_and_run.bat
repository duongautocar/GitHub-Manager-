@echo off
title GitHub Manager Pro v2.0.0
color 0A

echo ============================================
echo    GitHub Manager Pro
echo    Công cụ quản lý GitHub chuyên nghiệp
echo    Phiên bản: 2.0.0
echo ============================================
echo.

REM Kiểm tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python chua duoc cai dat!
    echo Vui long tai Python tu: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python da duoc cai dat.

REM Kiểm tra Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Git chua duoc cai dat!
    echo Vui long tai Git tu: https://git-scm.com
    echo.
)
echo [OK] Git da duoc cai dat.

REM Tạo môi trường ảo
if not exist "venv\" (
    echo [INFO] Dang tao moi truong ao...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Khong the tao moi truong ao!
        pause
        exit /b 1
    )
    echo [OK] Da tao moi truong ao.
)

REM Kích hoạt môi trường ảo
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Khong the kich hoat moi truong ao!
    pause
    exit /b 1
)
echo [OK] Da kich hoat moi truong ao.

REM Cài đặt thư viện
echo [INFO] Dang cai dat thu vien...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Khong the cai dat thu vien!
    pause
    exit /b 1
)
echo [OK] Da cai dat thu vien.

echo.
echo ============================================
echo    Dang khoi dong GitHub Manager Pro...
echo ============================================
echo.

REM Chạy ứng dụng
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Ung dung gap loi!
    echo Vui long kiem tra ket noi mang va thu lai.
    pause
)

REM Tắt môi trường ảo
deactivate