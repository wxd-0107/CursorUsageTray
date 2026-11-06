@echo off
setlocal
cd /d "%~dp0"

REM 无参双击时转 run.vbs，避免长期占用 CMD 窗口（仍可能闪一下）
if "%~1"=="" (
  wscript.exe //nologo "%~dp0run.vbs"
  exit /b 0
)

set "PY="
if exist "C:\Software\Python313\python.exe" set "PY=C:\Software\Python313\python.exe"
if not defined PY if exist "C:\Software\miniconda3\python.exe" set "PY=C:\Software\miniconda3\python.exe"
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)

if not defined PY (
  echo 未找到 Python，请安装 Python 3.10+ 并加入 PATH。
  pause
  exit /b 1
)

set "PYW=%PY%"
if /i "%PY:~-10%"=="python.exe" set "PYW=%PY:python.exe=pythonw.exe%"
if /i "%PYW%"=="python" set "PYW=pythonw"

"%PY%" -m pip install -r requirements.txt -q
"%PYW%" main.py
exit /b 0
