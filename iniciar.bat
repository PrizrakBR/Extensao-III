@echo off
chcp 65001 >nul
title TI Papanduva - Sistema de Estoque e Agendamentos
cd /d "%~dp0"

REM Detecta Python
where python >nul 2>&1
if %errorlevel% == 0 (
    python main.py
    goto :fim
)

where py >nul 2>&1
if %errorlevel% == 0 (
    py -3 main.py
    goto :fim
)

echo [ERRO] Python nao encontrado.
echo Execute o arquivo "instalar.bat" primeiro.
pause

:fim
