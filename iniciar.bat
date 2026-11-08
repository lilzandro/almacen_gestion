@echo off
title DigiCable - Sistema de Control de Inventarios
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Creando entorno virtual...
    python -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt
)
echo Iniciando aplicacion...
".venv\Scripts\python.exe" main.py
