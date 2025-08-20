"""
Common utilities and shared imports for the project
This module centralizes common imports and utilities to reduce duplication
"""

from decimal import Decimal, InvalidOperation
import logging
import os
import sys # Importar sys para StreamHandler
import functools # Importar functools para wraps
import traceback # Importar traceback para loggear stack traces
from pathlib import Path # Importar Path para manejo de rutas
from typing import Optional, Dict, Any, List, Tuple, Union
from mysql.connector import Error

# Configure logging
class ColoredFormatter(logging.Formatter):
    """Formatter personalizado con colores para la consola"""
    
    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Verde
        'WARNING': '\033[33m',   # Amarillo
        'ERROR': '\033[31m',     # Rojo
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Aplicar color solo si es para consola
        if hasattr(record, 'color_enabled') and record.color_enabled:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

def configure_application_logging(
    log_level=logging.DEBUG,
    log_file='app.log',
    max_file_size=10*1024*1024,  # 10MB
    backup_count=5,
    enable_console_colors=True
):
    """
    Configura el sistema de logging para toda la aplicación.
    Esta función debe llamarse UNA SOLA VEZ al inicio de la aplicación.
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Nombre del archivo de log
        max_file_size: Tamaño máximo del archivo antes de rotar (bytes)
        backup_count: Número de archivos de backup a mantener
        enable_console_colors: Habilitar colores en la consola
    """
    
    # Verificar si ya se configuró el logging root
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return  # Ya está configurado, no hacer nada
    
    # Crear directorio de logs si no existe
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    log_file_path = log_dir / log_file
    
    # Formato detallado para archivo
    file_format = (
        '%(asctime)s | %(name)-20s | %(levelname)-8s | '
        '[%(filename)s:%(lineno)d] | %(funcName)s() | %(message)s'
    )
    
    # Formato más limpio para consola
    console_format = (
        '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s'
    )
    
    # Configurar handler para archivo con rotación
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(file_format))
    
    # Configurar handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if enable_console_colors:
        console_formatter = ColoredFormatter(console_format)
        # Añadir flag para habilitar colores
        old_emit = console_handler.emit
        def colored_emit(record):
            record.color_enabled = True
            return old_emit(record)
        console_handler.emit = colored_emit
    else:
        console_formatter = logging.Formatter(console_format)
    
    console_handler.setFormatter(console_formatter)
    
    # Configurar el logger root
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log inicial para confirmar configuración
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("🚀 SISTEMA DE LOGGING CONFIGURADO EXITOSAMENTE")
    logger.info("=" * 60)
    logger.info(f"📁 Archivo de log: {log_file_path}")
    logger.info(f"📊 Nivel de log: {logging.getLevelName(log_level)}")
    logger.info(f"🎨 Colores en consola: {'✅' if enable_console_colors else '❌'}")
    logger.info(f"🔄 Rotación de archivos: {max_file_size // (1024*1024)}MB, {backup_count} backups")
    logger.debug("Configuración de logging completada exitosamente")

def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger para el módulo especificado.
    No reconfigura el sistema de logging, solo retorna el logger.
    
    Args:
        name: Nombre del módulo (usar __name__)
    
    Returns:
        Logger configurado para el módulo
    """
    return logging.getLogger(name)

def log_function_entry(logger: logging.Logger, func_name: str, **kwargs):
    """
    Registra la entrada a una función con sus parámetros.
    
    Args:
        logger: Logger del módulo
        func_name: Nombre de la función
        **kwargs: Parámetros de la función
    """
    if kwargs:
        params = ", ".join([f"{k}={_safe_repr(v)}" for k, v in kwargs.items()])
        logger.debug(f"🔵 ENTRADA → {func_name}({params})")
    else:
        logger.debug(f"🔵 ENTRADA → {func_name}()")

def log_function_exit(logger: logging.Logger, func_name: str, result=None, execution_time=None):
    """
    Registra la salida de una función con su resultado.
    
    Args:
        logger: Logger del módulo
        func_name: Nombre de la función
        result: Resultado de la función (opcional)
        execution_time: Tiempo de ejecución en segundos (opcional)
    """
    time_info = f" [{execution_time:.3f}s]" if execution_time else ""
    if result is not None:
        logger.debug(f"🔴 SALIDA ← {func_name}{time_info} → {_safe_repr(result)}")
    else:
        logger.debug(f"🔴 SALIDA ← {func_name}{time_info}")

def log_exception(logger: logging.Logger, func_name: str, exception: Exception, context: str = ""):
    """
    Registra una excepción con información detallada.
    
    Args:
        logger: Logger del módulo
        func_name: Nombre de la función donde ocurrió la excepción
        exception: La excepción capturada
        context: Contexto adicional sobre la excepción
    """
    context_info = f" | Contexto: {context}" if context else ""
    logger.error(f"💥 EXCEPCIÓN en {func_name}: {type(exception).__name__}: {exception}{context_info}")
    logger.debug(f"📋 Stack trace completo:\n{traceback.format_exc()}")

def log_performance(logger: logging.Logger, func_name: str, execution_time: float, threshold: float = 1.0):
    """
    Registra información de rendimiento de una función.
    
    Args:
        logger: Logger del módulo
        func_name: Nombre de la función
        execution_time: Tiempo de ejecución en segundos
        threshold: Umbral en segundos para considerar lento
    """
    if execution_time > threshold:
        logger.warning(f"⚠️ RENDIMIENTO: {func_name} tardó {execution_time:.3f}s (umbral: {threshold}s)")
    else:
        logger.debug(f"⚡ RENDIMIENTO: {func_name} completado en {execution_time:.3f}s")

def log_database_operation(logger: logging.Logger, operation: str, table: str, affected_rows: int = None, query: str = None):
    """
    Registra operaciones de base de datos.
    
    Args:
        logger: Logger del módulo
        operation: Tipo de operación (SELECT, INSERT, UPDATE, DELETE)
        table: Tabla afectada
        affected_rows: Número de filas afectadas
        query: Query SQL (opcional, solo para debug)
    """
    rows_info = f" | Filas: {affected_rows}" if affected_rows is not None else ""
    logger.info(f"🗄️ DB {operation} en tabla '{table}'{rows_info}")
    if query and logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"📝 Query: {query}")

def log_user_action(logger: logging.Logger, action: str, user: str = "system", details: str = ""):
    """
    Registra acciones del usuario.
    
    Args:
        logger: Logger del módulo
        action: Acción realizada
        user: Usuario que realizó la acción
        details: Detalles adicionales
    """
    details_info = f" | {details}" if details else ""
    logger.info(f"👤 ACCIÓN [{user}]: {action}{details_info}")

def logged_method(logger: logging.Logger = None, log_args: bool = True, log_result: bool = False, 
                 enable_performance: bool = False, performance_threshold: float = 1.0):
    """
    Decorador para logging automático de métodos.
    
    Args:
        logger: Logger a usar (si None, se obtiene del módulo)
        log_args: Si registrar argumentos de entrada
        log_result: Si registrar el resultado
        log_performance: Si registrar información de rendimiento
        performance_threshold: Umbral para considerar lento
    """
    from datetime import datetime # Importar datetime aquí para evitar circular
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener logger si no se proporcionó
            func_logger = logger or get_logger(func.__module__)
            func_name = f"{func.__qualname__}"
            
            # Log de entrada
            if log_args:
                # Filtrar 'self' de los argumentos para métodos de clase
                filtered_kwargs = kwargs.copy()
                if args and hasattr(args[0], '__class__'):
                    # Si es un método de instancia, el primer arg es 'self'.
                    # No lo incluimos en el log de parámetros explícitamente.
                    # Los kwargs ya son los parámetros nombrados.
                    log_function_entry(func_logger, func_name, **filtered_kwargs)
                else:
                    # Para funciones o métodos estáticos/de clase sin 'self'
                    all_args = dict(zip(func.__code__.co_varnames, args))
                    all_args.update(filtered_kwargs)
                    log_function_entry(func_logger, func_name, **all_args)
            else:
                func_logger.debug(f"🔵 ENTRADA → {func_name}")
            
            # Ejecutar función con medición de tiempo
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Log de salida
                if log_result:
                    log_function_exit(func_logger, func_name, result, execution_time)
                else:
                    log_function_exit(func_logger, func_name, execution_time=execution_time)
                
                # Log de rendimiento
                if enable_performance:
                    log_performance(func_logger, func_name, execution_time, performance_threshold)
                
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds() # Medir tiempo incluso en error
                log_exception(func_logger, func_name, e)
                raise # Re-lanzar la excepción para no alterar el flujo del programa
                
        return wrapper
    return decorator

def _safe_repr(obj: Any, max_length: int = 100) -> str:
    """
    Representación segura de objetos para logging.
    
    Args:
        obj: Objeto a representar
        max_length: Longitud máxima de la representación
    
    Returns:
        Representación string del objeto
    """
    try:
        if obj is None:
            return "None"
        elif isinstance(obj, (str, int, float, bool)):
            repr_str = repr(obj)
        elif isinstance(obj, Decimal):
            repr_str = f"Decimal('{obj}')"
        elif isinstance(obj, (list, tuple, dict)):
            if len(str(obj)) > max_length:
                repr_str = f"{type(obj).__name__}[{len(obj)} items]"
            else:
                repr_str = repr(obj)
        else:
            repr_str = f"<{type(obj).__name__} object>"
        
        # Truncar si es muy largo
        if len(repr_str) > max_length:
            repr_str = repr_str[:max_length-3] + "..."
        
        return repr_str
    except Exception:
        return f"<{type(obj).__name__} object - repr failed>"

# Common decimal operations
def safe_decimal(value: Any, default: Decimal = Decimal('0.00')) -> Decimal:
    """Safely convert value to Decimal"""
    try:
        if value is None:
            return default
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default

# Common validation
def validate_not_empty(value: str, field_name: str) -> bool:
    """Validate that a string is not empty"""
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
    return True

# Common database patterns
def format_currency(amount: Decimal) -> str:
    """Format decimal as currency string"""
    return f"${amount:.2f}"

def parse_currency(value: str) -> Decimal:
    """Parse currency string to Decimal"""
    if not value:
        return Decimal('0.00')
    # Remove currency symbols and commas
    clean_value = str(value).replace('$', '').replace(',', '')
    return safe_decimal(clean_value)

