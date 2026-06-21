@echo off
setlocal EnableExtensions

REM Klik dua kali file ini dari Windows Explorer.
REM File ini harus berada dalam folder yang sama dengan app.py.
cd /d "%~dp0"

set "PYTHON_CMD="

where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py"

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    where python3 >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python3"
)

if not exist "app.py" (
    echo.
    echo app.py tidak ditemukan.
    echo Simpan start_dashboard_windows.bat di folder yang sama dengan app.py.
    echo.
    pause
    exit /b 1
)

if not defined PYTHON_CMD (
    echo.
    echo Python belum terdeteksi.
    echo Install Python 3 dari https://www.python.org/downloads/windows/
    echo Saat instalasi, centang Add python.exe to PATH.
    echo Tutup jendela ini lalu jalankan file BAT lagi.
    echo.
    pause
    exit /b 1
)

echo.
echo ==============================================
echo Customer Churn at Beauti Clinic - Dashboard
echo Perintah Python: %PYTHON_CMD%
echo ==============================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Menyiapkan folder Python pertama kali...
    %PYTHON_CMD% -m venv ".venv"
    if errorlevel 1 (
        echo.
        echo Folder .venv gagal dibuat.
        echo Pastikan Python 3 terpasang, lalu jalankan ulang.
        echo.
        pause
        exit /b 1
    )
)

set "VENV_PY=.venv\Scripts\python.exe"

echo Memeriksa library dashboard...
"%VENV_PY%" -m pip install --disable-pip-version-check --upgrade pip
"%VENV_PY%" -m pip install --disable-pip-version-check -r requirements_dashboard.txt
if errorlevel 1 (
    echo.
    echo Library gagal dipasang. Cek koneksi internet lalu jalankan ulang.
    echo.
    pause
    exit /b 1
)

echo.
echo Dashboard akan terbuka di browser.
echo Bila browser belum terbuka, buka http://localhost:8501
echo Jangan tutup jendela ini selama dashboard dipakai.
echo Tekan Ctrl + C untuk menghentikan dashboard.
echo.

"%VENV_PY%" -m streamlit run app.py

echo.
echo Dashboard dihentikan.
pause
