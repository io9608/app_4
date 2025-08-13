import mysql.connector
from mysql.connector import Error
from decimal import Decimal

class Autoconsumo:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def registrar_autoconsumo(self, producto_id: int, cantidad: Decimal, unidad: str, motivo: str = None) -> bool:
        """
        Registra un autoconsumo de un producto.
        """
        if not isinstance(producto_id, int) or producto_id <= 0:
            raise ValueError("El ID del producto debe ser un entero positivo.")
        if not isinstance(cantidad, Decimal) or cantidad <= Decimal('0'):
            raise ValueError("La cantidad debe ser un número decimal positivo.")
        if not unidad or not isinstance(unidad, str):
            raise ValueError("La unidad no puede estar vacía y debe ser una cadena de texto.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            # Iniciar transacción
            conn.start_transaction()
            
            cursor = conn.cursor()
            
            # Obtener el costo promedio del producto
            cursor.execute("SELECT total_invertido, cantidad FROM productos WHERE id = %s", (producto_id,))
            result = cursor.fetchone()
            
            if not result:
                raise ValueError("Producto no encontrado.")
                
            total_invertido, cantidad_actual = result
            
            # Calcular costo promedio
            if cantidad_actual > Decimal('0'):
                costo_promedio = total_invertido / cantidad_actual
            else:
                costo_promedio = Decimal('0')
                
            costo_total = cantidad * costo_promedio
            
            # Insertar registro de autoconsumo
            query = """
                INSERT INTO autoconsumo (producto_id, cantidad, unidad, motivo, costo)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (producto_id, cantidad, unidad, motivo, costo_total))
            
            # Reducir la cantidad en el inventario
            cursor.execute(
                "UPDATE productos SET cantidad = cantidad - %s WHERE id = %s",
                (cantidad, producto_id)
            )
            
            # Confirmar transacción
            conn.commit()
            return True
            
        except Error as e:
            if conn:
                conn.rollback()
            raise e
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()

    def obtener_historial_autoconsumo(self, dias: int = 30) -> list:
        """
        Obtiene el historial de autoconsumo de los últimos días especificados.
        """
        try:
            query = """
                SELECT a.id, p.nombre_producto, a.cantidad, a.unidad, a.motivo, a.fecha_autoconsumo, a.costo
                FROM autoconsumo a
                JOIN productos p ON a.producto_id = p.id
                WHERE a.fecha_autoconsumo >= DATE_SUB(NOW(), INTERVAL %s DAY)
                ORDER BY a.fecha_autoconsumo DESC
            """
            results = self.db_connection.fetch_all(query, (dias,))
            
            historial = []
            column_names = ["id", "nombre_producto", "cantidad", "unidad", "motivo", "fecha_autoconsumo", "costo"]
            
            for row in results:
                entry_dict = dict(zip(column_names, row))
                entry_dict['cantidad'] = Decimal(str(entry_dict['cantidad']))
                entry_dict['costo'] = Decimal(str(entry_dict['costo']))
                historial.append(entry_dict)
                
            return historial
            
        except Exception as e:
            raise e

    def obtener_total_costo_autoconsumo(self, dias: int = 30) -> Decimal:
        """
        Obtiene el costo total de autoconsumo en los últimos días especificados.
        """
        try:
            query = """
                SELECT COALESCE(SUM(costo), 0)
                FROM autoconsumo
                WHERE fecha_autoconsumo >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            result = self.db_connection.fetch_one(query, (dias,))
            
            if result and result[0] is not None:
                return Decimal(str(result[0]))
            return Decimal('0.00')
            
        except Exception as e:
            raise e
