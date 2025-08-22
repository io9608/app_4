# 🚀 Instrucciones de Lanzamiento

Este documento proporciona instrucciones para ejecutar el Sistema de Gestión Comercial en diferentes sistemas operativos.

## 📋 Tabla de Contenidos
- [Linux/macOS](#linuxmacos)
- [Windows](#windows)
- [Crear .exe para Windows](#crear-exe-para-windows)
- [Solución de Problemas](#solución-de-problemas)

---

## Linux/macOS

### Método 1: Usar el script launcher.sh (Recomendado)
```bash
# Hacer el script ejecutable (solo la primera vez)
chmod +x launcher.sh

# Ejecutar el launcher
./launcher.sh

# O con permisos de administrador si es necesario
sudo ./launcher.sh
```

### Método 2: Ejecutar directamente
```bash
python3 app.py
```

### Método 3: Con entorno virtual
```bash
# Activar entorno virtual (si existe)
source venv/bin/activate

# Ejecutar
python app.py
```

---

## Windows

### Método 1: Usar el archivo .bat (Recomendado)
1. Haz doble clic en `launcher.bat`
2. O abre CMD/PowerShell y ejecuta:
```cmd
launcher.bat
```

### Método 2: Ejecutar directamente
```cmd
python app.py
```

### Método 3: Con entorno virtual
```cmd
# Activar entorno virtual
venv\Scripts\activate

# Ejecutar
python app.py
```

---

## Crear .exe para Windows

### Opción 1: Usar el script create_exe.py (Automático)
```cmd
# Instalar PyInstaller
pip install pyinstaller

# Ejecutar el script creador
python create_exe.py
```

### Opción 2: Manual con PyInstaller
```cmd
# Instalar PyInstaller
pip install pyinstaller

# Crear ejecutable
pyinstaller --onefile --windowed --name=SistemaGestionComercial app.py

# El ejecutable estará en: dist/SistemaGestionComercial.exe
```

### Opción 3: Con icono personalizado
```cmd
# Crear un icono .ico (opcional)
# Luego ejecutar:
pyinstaller --onefile --windowed --icon=icon.ico --name=SistemaGestionComercial app.py
```

---

## Solución de Problemas

### Error: "Python no encontrado"
- **Linux/macOS**: Instala Python3 con `sudo apt install python3` o `brew install python3`
- **Windows**: Descarga desde https://www.python.org/downloads/

### Error: "tkinter no encontrado"
- **Ubuntu/Debian**: `sudo apt install python3-tk`
- **CentOS/RHEL**: `sudo yum install python3-tkinter`
- **Windows**: Reinstala Python marcando "tcl/tk and IDLE"

### Error: "Permiso denegado" en Linux
```bash
chmod +x launcher.sh
```

### Error: "No se encuentra app.py"
Asegúrate de ejecutar los launchers desde el directorio raíz del proyecto.

### Error: "Módulos no encontrados"
```bash
# Instalar dependencias
pip install -r requirements.txt
```

---

## 📁 Estructura de Archivos
```
proyecto/
├── app.py                    # Archivo principal
├── launcher.sh               # Script para Linux/macOS
├── launcher.bat              # Script para Windows
├── create_exe.py             # Creador de .exe
├── LAUNCHER_INSTRUCTIONS.md  # Este archivo
├── Core/                     # Módulos del sistema
├── Gui/                      # Interfaz gráfica
└── venv/                     # Entorno virtual (opcional)
```

---

## 🎯 Resumen Rápido

| Sistema | Método Principal | Comando |
|---------|------------------|---------|
| Linux   | launcher.sh      | `./launcher.sh` |
| macOS   | launcher.sh      | `./launcher.sh` |
| Windows | launcher.bat     | `launcher.bat` |
| Windows | .exe             | `SistemaGestionComercial.exe` |

---

## 🆘 Soporte
Si encuentras problemas:
1. Verifica que Python esté instalado: `python --version`
2. Asegúrate de estar en el directorio correcto
3. Comprueba que todos los archivos estén presentes
4. Para Windows: ejecuta como administrador si es necesario
