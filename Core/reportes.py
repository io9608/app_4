import mysql.connector
from mysql.connector import Error
from Core.recetas import RecetasManager # CAMBIO: Importar RecetasManager
from Core.productos import Productos
from decimal import Decimal

class Reportes:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.recetas_manager = RecetasManager(db_connection) # CAMBIO: Usar RecetasManager
        self.productos_manager = Productos(db_connection)

    def calcular_costo_por_unidad(self, receta_id): # CAMBIO: receta_id
        """Calcula el costo por unidad de una receta basado en sus ingredientes."""
        # Convertir receta_id a entero si viene como "ID - Nombre"
        if isinstance(receta_id, str) and ' - ' in receta_id:
            receta_id = int(receta_id.split(' - ')[0])

        # Usar el método de RecetasManager para calcular el costo
        try:
            costo_total_receta = self.recetas_manager.calcular_costo_receta(receta_id, self.productos_manager)
            return costo_total_receta
        except Exception as e:
            print(f"Error al calcular costo por unidad de receta {receta_id}: {e}")
            return Decimal('0.00')

    def calcular_ganancia_por_unidad(self, receta_id, precio_venta): # CAMBIO: receta_id
        """Calcula la ganancia por unidad de una receta."""
        costo_por_unidad = self.calcular_costo_por_unidad(receta_id)
        ganancia = Decimal(str(precio_venta)) - costo_por_unidad
        return ganancia

    def obtener_ventas_por_producto(self):
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            # CAMBIO: Unir con la tabla 'recetas' en lugar de 'productos' para ventas de recetas
            cursor.execute("""
                SELECT r.nombre, SUM(v.cantidad_vendida) as total_vendido, SUM(v.precio_venta * v.cantidad_vendida) as total_ingresos
                FROM ventas v
                JOIN recetas r ON v.producto_id = r.id
                GROUP BY r.id
                ORDER BY total_ingresos DESC
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener ventas por producto: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def obtener_clientes_top(self):
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.cliente_nombre, COUNT(v.id) as total_compras, SUM(v.precio_venta * v.cantidad_vendida) as total_gastado
                FROM ventas v
                WHERE v.cliente_nombre IS NOT NULL AND v.cliente_nombre != ''
                GROUP BY v.cliente_nombre
                ORDER BY total_gastado DESC
                LIMIT 10
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener clientes top: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def obtener_productos_bajo_stock(self):
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nombre_producto, stock_minimo, cantidad
                FROM productos
                WHERE cantidad < stock_minimo
                ORDER BY nombre_producto
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener productos bajo stock: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def obtener_ventas_semanales(self):
        """Obtiene las ventas de los últimos 7 días"""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DATE(v.fecha_venta) as fecha, 
                       COALESCE(SUM(v.precio_venta * v.cantidad_vendida), 0) as total
                FROM ventas v
                WHERE v.fecha_venta >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(v.fecha_venta)
                ORDER BY fecha
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener ventas semanales: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def obtener_ganancias_por_receta(self):
        """Obtiene las ganancias por receta"""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.nombre,
                       COALESCE(SUM(v.cantidad_vendida), 0) as cantidad_vendida,
                       COALESCE(SUM(v.precio_venta * v.cantidad_vendida), 0) as ingresos,
                       COALESCE(SUM(v.cantidad_vendida * (
                           (SELECT COALESCE(SUM(ri.cantidad * p.total_invertido / p.cantidad), 0)
                            FROM receta_ingredientes ri
                            JOIN productos p ON ri.ingrediente_id = p.id
                            WHERE ri.receta_id = r.id)
                       )), 0) as costos_ingredientes,
                       COALESCE(SUM(v.cantidad_vendida * r.costo_mano_obra_total), 0) as costos_mano_obra
                FROM recetas r
                LEFT JOIN ventas v ON r.id = v.producto_id
                GROUP BY r.id, r.nombre, r.costo_mano_obra_total
                ORDER BY ingresos DESC
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener ganancias por receta: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def obtener_total_ventas(self):
        """Obtiene el total de ventas"""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(v.precio_venta * v.cantidad_vendida), 0)
                FROM ventas v
            """)
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else 0
        except Error as e:
            print(f"Error al obtener total de ventas: {e}")
            return 0
        finally:
            if cursor: cursor.close()

    def obtener_total_costos(self):
        """Obtiene el total de costos"""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(ri.cantidad * p.total_invertido / p.cantidad), 0)
                FROM ventas v
                JOIN recetas r ON v.producto_id = r.id
                JOIN receta_ingredientes ri ON r.id = ri.receta_id
                JOIN productos p ON ri.ingrediente_id = p.id
            """)
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else 0
        except Error as e:
            print(f"Error al obtener total de costos: {e}")
            return 0
        finally:
            if cursor: cursor.close()
