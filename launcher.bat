@echo off
REM Sistema de Gestión Comercial - Windows Launcher
REM Compatible con Windows 10/11

title Sistema de Gestión Comercial
color 0A

echo.
echo [92m🚀 Iniciando Sistema de Gestión Comercial[0m
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [91m❌ Python no está instalado o no está en el PATH[0m
    echo.
    echo Por favor instala Python desde: https://www.python.org/downloads/
    echo Asegúrate de marcar "Add Python to PATH" durante la instalación
    pause
    exit /b 1
)

REM Verificar si estamos en el directorio correcto
if not exist "app.py" (
    echo [91m❌ No se encontró app.py en el directorio actual[0m
    echo Por favor ejecuta este script desde el directorio raíz del proyecto
    pause
    exit /b 1
)

REM Verificar dependencias básicas
echo [93m📦 Verificando dependencias...[0m
python -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo [91m❌ tkinter no está disponible[0m
    echo Por favor instala Python con soporte para tkinter
    pause
    exit /b 1
)

REM Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    echo [92m✅ Activando entorno virtual...[0m
    call venv\Scripts\activate.bat
)

REM Ejecutar la aplicación
echo [92m✅ Iniciando aplicación...[0m
python app.py %*

echo.
echo [92m👋 Aplicación cerrada[0m
pause
