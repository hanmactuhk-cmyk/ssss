@echo off
setlocal
python -m pip install -r requirements.txt || exit /b 1
python -m playwright install chromium || exit /b 1
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
python -m PyInstaller --noconfirm --clean --windowed --name G-Labs-Flow-Automation --collect-all PySide6 --collect-all playwright app\main.py || exit /b 1
xcopy /E /I /Y data dist\G-Labs-Flow-Automation\data >nul
xcopy /E /I /Y app dist\G-Labs-Flow-Automation\app >nul
copy /Y README.md dist\G-Labs-Flow-Automation\README.md >nul
 echo Build complete: dist\G-Labs-Flow-Automation
pause
