import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración de la aplicación"""
    
    # Configuración de Base de Datos - MariaDB
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))  # MariaDB default port
    DB_NAME = os.getenv('DB_NAME', 'gestion_negocio')
    DB_USER = os.getenv('DB_USER', 'pp')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '1234')
    
    # Configuración de la Aplicación
    SECRET_KEY = os.getenv('APP_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('APP_DEBUG', 'True').lower() == 'true'
    
    # Configuración de Entorno
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # Configuración de Stock
    MIN_STOCK_VISIBLE = 0  # Productos con stock <= 0 no se mostrarán
    
    # Database connection string for MariaDB
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    ENVIRONMENT = 'production'

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    ENVIRONMENT = 'development'

class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    ENVIRONMENT = 'testing'
