@echo off
reg add HKEY_CURRENT_USER\Console /v QuickEdit /t REG_DWORD /d 00000000 /f
python app.py runserver --host 0.0.0.0 --port 8001
pause
