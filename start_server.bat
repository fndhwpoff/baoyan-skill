@echo off
cd /d "%~dp0"
"D:\Program Files\Python310\python.exe" -u tools\web_server.py --port 8765 > server.log 2>&1
