@echo off
setlocal
set "PYTHON_BIN=%~dp0Python\cpython-3.12.11-windows-x86_64-none\python.exe"
if not exist "%PYTHON_BIN%" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap-python.ps1"
  if errorlevel 1 exit /b 1
)
if "%~1"=="" goto interactive
"%PYTHON_BIN%" -I -X utf8 "%~dp0deploy.py" --run %*
exit /b %errorlevel%

:interactive
"%PYTHON_BIN%" -I -X utf8 "%~dp0deploy.py" --run check
set "RESULT=%errorlevel%"
pause
exit /b %RESULT%
