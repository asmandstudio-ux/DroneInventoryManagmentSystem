@echo off
setlocal
cd /d "%~dp0.."

REM Usage:
REM   .\release\run.cmd ps
REM   .\release\run.cmd logs backend

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" %*
exit /b %ERRORLEVEL%
