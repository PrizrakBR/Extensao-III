@echo off
chcp 65001 >nul
title Instalador - TI Papanduva

echo.
echo ============================================================
echo   SISTEMA DE ESTOQUE E AGENDAMENTOS - TI PAPANDUVA
echo   Instalador de Dependencias
echo ============================================================
echo.

REM Verifica se Python está instalado
where python >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python encontrado.
    goto :install_deps
)

REM Tenta com py launcher
where py >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python (py launcher) encontrado.
    set PYTHON_CMD=py -3
    goto :install_deps
)

echo [!] Python nao encontrado. Iniciando instalacao automatica...
echo.
echo Instalando Python 3.11 via winget...
winget install -e --id Python.Python.3.11 --accept-source-agreements --accept-package-agreements
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha ao instalar Python automaticamente.
    echo Acesse: https://www.python.org/downloads/
    echo Baixe e instale o Python 3.x marcando a opcao "Add Python to PATH".
    pause
    exit /b 1
)
echo.
echo [OK] Python instalado. Reiniciando instalacao...
echo Por favor, feche este janela e execute novamente o instalar.bat
pause
exit /b 0

:install_deps
echo.
echo Instalando dependencias Python...
echo.

REM Detecta comando Python
where python >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON_CMD=python
) else (
    set PYTHON_CMD=py -3
)

%PYTHON_CMD% -m pip install --upgrade pip >nul 2>&1
%PYTHON_CMD% -m pip install customtkinter
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar customtkinter
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Instalacao concluida com sucesso!
echo   Execute o arquivo "iniciar.bat" para abrir o sistema.
echo ============================================================
echo.
pause
