@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

echo [Bear-Chess] Installing build dependencies...
%PY% -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo [Bear-Chess] Failed to install dependencies.
    pause
    exit /b 1
)

echo [Bear-Chess] Building executable...
%PY% -m PyInstaller --noconfirm --clean --windowed --name BearChess ^
  --add-data "images;images" ^
  --add-data "engine;engine" ^
  --add-data "openings.json;." ^
  main.py

if errorlevel 1 (
    echo [Bear-Chess] Build failed.
    pause
    exit /b 1
)

echo [Bear-Chess] Build finished.
echo Output: dist\BearChess\BearChess.exe

echo [Bear-Chess] Creating desktop shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$desktop=[Environment]::GetFolderPath('Desktop'); $target=Join-Path $PWD 'launch_bear_chess_hidden.vbs'; $exe=Join-Path $PWD 'dist\BearChess\BearChess.exe'; $shortcut=Join-Path $desktop 'Bear Chess.lnk'; if (Test-Path $target) { $w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut($shortcut); $s.TargetPath=$target; $s.WorkingDirectory=$PWD; if (Test-Path $exe) { $s.IconLocation=$exe }; $s.Save(); Write-Output ('Shortcut: ' + $shortcut) } else { Write-Output 'Skip shortcut: launcher not found' }"

if exist "dist\BearChess\BearChess.exe" (
    echo [Bear-Chess] Launching app...
    start "" "dist\BearChess\BearChess.exe"
) else (
    echo [Bear-Chess] Executable not found in dist folder.
)

endlocal