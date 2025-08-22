#!/bin/bash

# Sistema de Gestión Comercial - Launcher Script
# Compatible con Linux y macOS

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando Sistema de Gestión Comercial${NC}"

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 no está instalado${NC}"
    echo "Por favor instala Python3:"
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  CentOS/RHEL: sudo yum install python3"
    echo "  macOS: brew install python3"
    exit 1
fi

# Verificar si estamos en el directorio correcto
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ No se encontró app.py en el directorio actual${NC}"
    echo "Por favor ejecuta este script desde el directorio raíz del proyecto"
    exit 1
fi

# Verificar dependencias básicas
echo -e "${YELLOW}📦 Verificando dependencias...${NC}"
python3 -c "import tkinter" 2>/dev/null || {
    echo -e "${RED}❌ tkinter no está disponible${NC}"
    echo "Por favor instala tkinter:"
    echo "  Ubuntu/Debian: sudo apt install python3-tk"
    echo "  CentOS/RHEL: sudo yum install python3-tkinter"
    exit 1
}

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Activando entorno virtual...${NC}"
    source venv/bin/activate
fi

# Ejecutar la aplicación
echo -e "${GREEN}✅ Iniciando aplicación...${NC}"
python3 app.py "$@"

# Desactivar entorno virtual si estaba activado
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

echo -e "${GREEN}👋 Aplicación cerrada${NC}"
