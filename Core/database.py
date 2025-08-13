import mysql.connector
from mysql.connector import Error, pooling
import sys
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Database:
    def __init__(self):
        # Use environment variables with fallbacks
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'gestion_negocio'),
            'user': os.getenv('DB_USER', 'pp'),
            'password': os.getenv('DB_PASSWORD', '1234'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': False
        }
        self.pool = None
        self._setup_connection_pool()

    def _setup_connection_pool(self):
        """Setup connection pooling for better performance"""
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="business_pool",
                pool_size=5,
                **self.config
            )
            logger.info("Database connection pool established")
        except Error as e:
            logger.error(f"Failed to setup connection pool: {e}")
            raise

    def get_connection(self):
        """Get connection from pool"""
        try:
            return self.pool.get_connection()
        except Error as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise

    def execute_query(self, query, params=None):
        """Execute query with proper error handling"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor, connection
        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def fetch_one(self, query, params=None):
        """Fetch single record"""
        cursor = None
        connection = None
        try:
            cursor, connection = self.execute_query(query, params)
            result = cursor.fetchone()
            connection.commit()
            return result
        except Error as e:
            logger.error(f"Fetch one failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def fetch_all(self, query, params=None):
        """Fetch all records"""
        cursor = None
        connection = None
        try:
            cursor, connection = self.execute_query(query, params)
            result = cursor.fetchall()
            connection.commit()
            return result
        except Error as e:
            logger.error(f"Fetch all failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def execute_update(self, query, params=None):
        """Execute update/insert/delete with transaction support"""
        cursor = None
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            connection.commit()
            return cursor.lastrowid
        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"Update failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def close_connection(self):
        """Close all connections in pool"""
        if self.pool:
            self.pool.close()
            logger.info("Database connection pool closed")
