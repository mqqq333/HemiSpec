@echo off
setlocal
cd /d "%~dp0\.."
set "PYTHONPATH=src"
if "%HEMISPEC_D2L_PYTHON%"=="" (
  echo Set HEMISPEC_D2L_PYTHON to the Python executable in your torch-enabled environment.
  echo Example: set HEMISPEC_D2L_PYTHON=C:\path\to\env\python.exe
  exit /b 1
)
"%HEMISPEC_D2L_PYTHON%" -m hemispec.gui
