#!/usr/bin/env python3
"""
Script para crear un ejecutable .exe para Windows usando PyInstaller
"""

import os
import sys
import subprocess
import shutil

def create_windows_exe():
    """Crea un ejecutable .exe para Windows"""
    
    print("🚀 Creando ejecutable .exe para Windows...")
    
    # Verificar si estamos en Windows
    if sys.platform != "win32":
        print("⚠️  Este script está diseñado para ejecutarse en Windows")
        print("   Para crear un .exe en Linux/macOS, usa PyInstaller directamente")
        return
    
    # Verificar si PyInstaller está instalado
    try:
        import PyInstaller
    except ImportError:
        print("❌ PyInstaller no está instalado")
        print("   Instalando PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Limpiar builds anteriores
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Comando para crear el ejecutable
    cmd = [
        "pyinstaller",
        "--onefile",                    # Un solo archivo ejecutable
        "--windowed",                   # Sin consola (GUI)
        "--name=SistemaGestionComercial", # Nombre del ejecutable
        "--icon=icon.ico",              # Icono (si existe)
        "--add-data=Core;Core",         # Incluir carpeta Core
        "--add-data=Gui;Gui",           # Incluir carpeta Gui
        "--add-data=logs;logs",         # Incluir carpeta logs
        "--hidden-import=tkinter",      # Importar tkinter
        "--hidden-import=sqlite3",      # Importar sqlite3
        "app.py"
    ]
    
    # Ejecutar PyInstaller
    try:
        subprocess.run(cmd, check=True)
        print("✅ Ejecutable creado exitosamente!")
        print(f"📁 Ubicación: {os.path.abspath('dist/SistemaGestionComercial.exe')}")
        
        # Crear acceso directo en el escritorio
        create_desktop_shortcut()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al crear el ejecutable: {e}")
        print("   Asegúrate de tener PyInstaller instalado correctamente")

def create_desktop_shortcut():
    """Crea un acceso directo en el escritorio de Windows"""
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "Sistema Gestión Comercial.lnk")
        target = os.path.abspath("dist/SistemaGestionComercial.exe")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.IconLocation = target
        shortcut.save()
        
        print("✅ Acceso directo creado en el escritorio")
        
    except ImportError:
        print("⚠️  No se pudo crear el acceso directo automáticamente")
        print("   Puedes crearlo manualmente apuntando a: dist/SistemaGestionComercial.exe")

if __name__ == "__main__":
    create_windows_exe()
