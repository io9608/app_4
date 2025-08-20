import mysql.connector
from mysql.connector import Error, pooling
import logging
import os
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Tuple, Union
from decimal import Decimal
import threading
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Enhanced database manager with proper connection pooling,
    transaction management, and error handling.
    
    This class addresses the issues found in the original Database class:
    1. Fixes "Unread result found" errors
    2. Fixes "'MySQLConnectionPool' object has no attribute 'close'" error
    3. Provides proper connection lifecycle management
    4. Adds transaction support with context managers
    5. Improves error handling and logging
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize database manager with configuration"""
        self.config = config or self._load_config()
        self.pool = None
        self._lock = threading.Lock()
        self._setup_connection_pool()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration from environment variables"""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'gestion_negocio'),
            'user': os.getenv('DB_USER', 'pp'),
            'password': os.getenv('DB_PASSWORD', '1234'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': False,
            'use_unicode': True,
            'raise_on_warnings': True
        }
    
    def _setup_connection_pool(self):
        """Setup connection pooling with proper configuration"""
        try:
            with self._lock:
                self.pool = pooling.MySQLConnectionPool(
                    pool_name="business_pool",
                    pool_size=10,
                    pool_reset_session=True,
                    **self.config
                )
                logger.info("Database connection pool established successfully")
        except Error as e:
            logger.error(f"Failed to setup connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        connection = None
        try:
            connection = self.pool.get_connection()
            yield connection
        except Error as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise
        finally:
            if connection:
                try:
                    connection.close()  # Return to pool, not close permanently
                except Error as e:
                    logger.error(f"Error returning connection to pool: {e}")
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        with self.get_connection() as conn:
            try:
                conn.start_transaction()
                yield conn
                conn.commit()
                logger.debug("Transaction committed successfully")
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
                raise
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute SELECT query and return results as dictionaries
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries with column names as keys
        """
        with self.get_connection() as conn:
            cursor = None
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                
                # Convert Decimal values to Decimal type
                for row in results:
                    for key, value in row.items():
                        if isinstance(value, str) and self._is_decimal(value):
                            row[key] = Decimal(value)
                        elif isinstance(value, float):
                            row[key] = Decimal(str(value))
                
                return results
            except Error as e:
                logger.error(f"Query execution failed: {e}")
                raise
            finally:
                if cursor:
                    cursor.close()
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Execute INSERT/UPDATE/DELETE query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = None
            try:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                affected_rows = cursor.rowcount
                conn.commit()
                return affected_rows
            except Error as e:
                conn.rollback()
                logger.error(f"Update query failed: {e}")
                raise
            finally:
                if cursor:
                    cursor.close()
    
    def execute_insert(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Execute INSERT query and return last insert ID
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Last insert ID
        """
        with self.get_connection() as conn:
            cursor = None
            try:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                last_id = cursor.lastrowid
                conn.commit()
                return last_id
            except Error as e:
                conn.rollback()
                logger.error(f"Insert query failed: {e}")
                raise
            finally:
                if cursor:
                    cursor.close()
    
    def fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
        """Fetch single record as dictionary"""
        results = self.execute_query(query, params)
        return results[0] if results else None
    
    def fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Fetch all records as dictionaries"""
        return self.execute_query(query, params)
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        Execute query with multiple parameter sets
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = None
            try:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                affected_rows = cursor.rowcount
                conn.commit()
                return affected_rows
            except Error as e:
                conn.rollback()
                logger.error(f"Execute many failed: {e}")
                raise
            finally:
                if cursor:
                    cursor.close()
    
    def _is_decimal(self, value: str) -> bool:
        """Check if string can be converted to Decimal"""
        try:
            Decimal(value)
            return True
        except (ValueError, ArithmeticError):
            return False
    
    def ping(self) -> bool:
        """Check database connectivity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return True
        except Exception as e:
            logger.error(f"Database ping failed: {e}")
            return False
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status"""
        if self.pool:
            return {
                'pool_name': self.pool.pool_name,
                'pool_size': self.pool.pool_size,
                'active_connections': len(self.pool._cnx_queue),
                'max_connections': self.pool.pool_size
            }
        return {'status': 'not_initialized'}
    
    def close_pool(self):
        """Close all connections in pool (for application shutdown)"""
        if self.pool:
            try:
                # MySQLConnectionPool doesn't have a close method
                # We just let the garbage collector handle it
                logger.info("Database pool marked for cleanup")
                self.pool = None
            except Exception as e:
                logger.error(f"Error during pool cleanup: {e}")


