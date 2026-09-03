@echo off
setlocal

set "OUTPUT_DIR=%~dp0dist"

uv run --with cx_Freeze python setup.py build_exe --build-exe "%OUTPUT_DIR%"

pause
