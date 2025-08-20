# MultipleFiles/database.py
import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self):
        self.host = 'localhost'
        self.database = 'gestion_negocio'
        self.user = 'pp'
        self.password = '1234'
        self.connection = None
        self.cursor = None # Añadir un cursor persistente

    def connect(self):
        if self.connection is None or not self.connection.is_connected():
            try:
                self.connection = mysql.connector.connect(
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
                # CAMBIO CLAVE: Crear el cursor aquí y mantenerlo abierto
                self.cursor = self.connection.cursor() 
                print("Conexión a la base de datos establecida.") # Para depuración
            except Error as e:
                print(f"Error al conectar a MariaDB: {e}")
                self.connection = None # Asegurarse de que sea None si falla
                self.cursor = None
        return self.connection

    def get_connection(self):
        """Devuelve la conexión a la base de datos."""
        if self.connection is None or not self.connection.is_connected():
            self.connect()
        return self.connection

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            # CAMBIO: Verificar si el cursor existe antes de cerrarlo
            if self.cursor:
                self.cursor.close()
                self.cursor = None # Resetear el cursor a None
            self.connection.close()
            self.connection = None
            # print("Conexión a la base de datos cerrada.")

    def execute_query(self, query, params=None):
        self.connect() # Asegurarse de que la conexión esté activa
        if self.connection and self.cursor: # Asegurarse de que el cursor también esté activo
            try:
                self.cursor.execute(query, params or ())
                # No hacemos commit aquí, lo haremos explícitamente en los managers
                return self.cursor # Devolver el cursor para que se puedan hacer fetch_one/all
            except Error as e:
                print(f"Error en la consulta: {e}") # Para depuración
                # No hacemos rollback aquí, lo haremos explícitamente en los managers
                raise e # Relanzar la excepción para que el manager la maneje
        else:
            raise Error("Cursor is not connected or connection is closed.") # Lanzar un error si el cursor no está listo

    def fetch_one(self, query, params=None):
        # CAMBIO CLAVE: No cerrar el cursor aquí. El cursor es persistente.
        cursor = self.execute_query(query, params)
        if cursor:
            result = cursor.fetchone()
            return result
        return None

    def fetch_all(self, query, params=None):
        # CAMBIO CLAVE: No cerrar el cursor aquí. El cursor es persistente.
        cursor = self.execute_query(query, params)
        if cursor:
            result = cursor.fetchall()
            return result
        return []

    def commit(self):
        if self.connection and self.connection.is_connected():
            try:
                self.connection.commit()
                print("Transacción confirmada.")
            except Error as e:
                print(f"Error al confirmar la transacción: {e}")
                raise e # Relanzar la excepción

    def rollback(self):
        if self.connection and self.connection.is_connected():
            try:
                self.connection.rollback()
                print("Transacción revertida.")
            except Error as e:
                print(f"Error al revertir la transacción: {e}")
                raise e # Relanzar la excepción

    def close_connection(self):
        """Cierra la conexión a la base de datos si está abierta."""
        self.disconnect()

