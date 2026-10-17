@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 START_PREVIEW.py
) else (
  python START_PREVIEW.py
)
pause
