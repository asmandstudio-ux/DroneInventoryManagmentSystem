@echo off
setlocal

set "DIR=%~dp0"
title DroneIMS Launcher
pushd "%DIR%" >NUL
echo.
echo Starting DroneIMS...
echo Opening startup screen...
echo.
if exist "%DIR%splash.html" (
  start "" "%DIR%splash.html"
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%DIR%DroneIMS.ps1"
if errorlevel 1 (
  echo.
  echo DroneIMS failed to start. See messages above.
  echo.
  pause
  popd >NUL
  exit /b 1
)

echo.
echo DroneIMS is starting in the background.
echo If the browser doesn't open, you can use:
echo   - Startup screen: %DIR%splash.html
echo   - App: http://127.0.0.1:3000/login
echo.
timeout /t 2 >NUL
popd >NUL
endlocal
