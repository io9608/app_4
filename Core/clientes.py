from mysql.connector import Error

class Clientes:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def agregar_cliente(self, nombre: str, contacto: str, telefono: str = "", direccion: str = "", notas: str = "") -> int:
        """Agrega un nuevo cliente a la base de datos y devuelve su ID."""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO clientes (nombre, contacto, telefono, direccion, notas) 
                VALUES (%s, %s, %s, %s, %s)""",
                (nombre, contacto, telefono, direccion, notas)
            )
            client_id = cursor.lastrowid
            conn.commit()
            return client_id
        except Error as e:
            raise Exception(f"Error al agregar cliente: {str(e)}")
        finally:
            if 'cursor' in locals(): cursor.close()

    def obtener_cliente(self, cliente_id: int) -> dict:
        """Obtiene un cliente por ID."""
        try:
            result = self.db_connection.fetch_one(
                "SELECT * FROM clientes WHERE id = %s",
                (cliente_id,)
            )
            return {
                'id': result[0],
                'nombre': result[1],
                'contacto': result[2],
                'telefono': result[3],
                'direccion': result[4],
                'notas': result[5]
            } if result else None
        except Error as e:
            raise Exception(f"Error al obtener cliente: {str(e)}")

    def obtener_todos_clientes(self) -> list:
        """Obtiene todos los clientes registrados."""
        try:
            results = self.db_connection.fetch_all("SELECT * FROM clientes ORDER BY nombre")
            return [
                {'id': row[0], 'nombre': row[1], 'contacto': row[2], 
                 'telefono': row[3], 'direccion': row[4], 'notas': row[5]} 
                for row in results
            ]
        except Error as e:
            raise Exception(f"Error al obtener clientes: {str(e)}")
