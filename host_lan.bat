@echo off
setlocal

set PORT=8000

cd /d "%~dp0"

set LAN_IP=
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /R /C:"IPv4 Address"') do (
    for /f "tokens=* delims= " %%B in ("%%A") do (
        set LAN_IP=%%B
        goto :ip_found
    )
)

:ip_found

echo Hosting QuizUrself on your local network...
echo.
if defined LAN_IP (
    echo Open this on other devices on the same LAN:
    echo   http://%LAN_IP%:%PORT%
) else (
    echo Could not auto-detect your LAN IP.
    echo Open this on other devices on the same LAN:
    echo   http://YOUR-LAN-IP:%PORT%
    echo.
    echo To find your LAN IP on Windows, run:
    echo   ipconfig
)
echo.
echo Press Ctrl+C to stop the server.
echo.

python -m http.server %PORT% --bind 0.0.0.0

endlocal
