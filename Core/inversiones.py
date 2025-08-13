# Core/inversiones.py
import mysql.connector
from mysql.connector import Error
from decimal import Decimal # Importar Decimal

class Inversiones:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def calcular_inversion_total(self):
        """Calcula la inversión total en productos."""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(total_invertido) FROM productos
            """)
            result = cursor.fetchone()[0]
            return Decimal(str(result)) if result is not None else Decimal('0.00')
        except Error as e:
            print(f"Error al calcular inversión total: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def calcular_ganancias_totales(self):
        """Calcula las ganancias totales a partir de las ventas."""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            # Esta consulta asume que 'total_invertido' en 'productos' representa el costo de los productos vendidos.
            # Para un cálculo de ganancia más preciso, se necesitaría un registro de costo de ventas por cada venta.
            cursor.execute("""
                SELECT 
                    SUM(v.precio_venta * v.cantidad_vendida) - SUM(r.costo_mano_obra_total * v.cantidad_vendida)
                FROM ventas v
                JOIN recetas r ON v.producto_id = r.id
            """)
            # Nota: Usamos el costo_mano_obra_total de las recetas para calcular las ganancias.
            result = cursor.fetchone()[0]
            return Decimal(str(result)) if result is not None else Decimal('0.00')
        except Error as e:
            print(f"Error al calcular ganancias totales: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

