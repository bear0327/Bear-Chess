@echo off
setlocal
cd /d "%~dp0"

set "EXE=dist\BearChess\BearChess.exe"
set "BAT=start_app.bat"
set "VBS=launch_bear_chess_hidden.vbs"

if exist "%VBS%" (
    set "TARGET=%CD%\%VBS%"
    set "WORKDIR=%CD%"
) else (
    echo [Bear-Chess] No launch target found.
    echo Expected one of:
    echo   - %VBS%
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$desktop=[Environment]::GetFolderPath('Desktop'); $shortcut=Join-Path $desktop 'Bear Chess.lnk'; $target=$env:TARGET; $work=$env:WORKDIR; $exe=Join-Path $work 'dist\BearChess\BearChess.exe'; $w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut($shortcut); $s.TargetPath=$target; $s.WorkingDirectory=$work; if (Test-Path $exe) { $s.IconLocation=$exe }; $s.Save(); Write-Output ('Shortcut created: ' + $shortcut); Write-Output ('Target: ' + $target)"

if errorlevel 1 (
    echo [Bear-Chess] Failed to create desktop shortcut.
    pause
    exit /b 1
)

echo [Bear-Chess] Desktop shortcut is ready.
endlocal
