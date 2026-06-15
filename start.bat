@echo off
cd /d "%~dp0"
title Image Upscaler

echo ============================================
echo   Image Upscaler - easy launcher
echo ============================================
echo.

REM ---------- detect Python ----------
set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [X] Python was not found.
  echo.
  echo     Please install Python first:
  echo       https://www.python.org/downloads/
  echo.
  echo     IMPORTANT: On the installer screen, check
  echo       "Add python.exe to PATH"
  echo.
  echo     After installing, double-click start.bat again.
  echo.
  pause
  exit /b 1
)

REM ---------- dependencies (first run only) ----------
%PY% -c "import streamlit" >nul 2>nul
if errorlevel 1 (
  echo [1/3] Installing required packages... first run may take a few minutes
  %PY% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo [X] Failed to install packages.
    echo     Check your internet connection and try again.
    echo.
    pause
    exit /b 1
  )
) else (
  echo [1/3] Packages ... OK
)

REM ---------- AI engines (first run only) ----------
if exist "bin\realesrgan-ncnn-vulkan\realesrgan-ncnn-vulkan.exe" goto bin_ok
if exist "bin\waifu2x-ncnn-vulkan\waifu2x-ncnn-vulkan.exe" goto bin_ok
echo [2/3] Downloading AI upscaling engines... first run only (from GitHub)
powershell -NoProfile -ExecutionPolicy Bypass -File ".\setup.ps1" -Yes
goto bin_done
:bin_ok
echo [2/3] AI engines ... OK
:bin_done

REM ---------- launch ----------
echo.
echo [3/3] Starting... your browser will open at http://127.0.0.1:8520
echo       To quit, just close this black window.
echo.
%PY% -m streamlit run app.py
pause
