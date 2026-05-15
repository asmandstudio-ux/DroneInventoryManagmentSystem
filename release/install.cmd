@echo off
setlocal
cd /d "%~dp0.."

REM Wrapper to run PowerShell scripts even when ExecutionPolicy is restricted.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
exit /b %ERRORLEVEL%
