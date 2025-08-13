import mysql.connector
from mysql.connector import Error
from datetime import datetime
from decimal import Decimal
from Core.productos import Productos
from Core.recetas import RecetasManager

class Ventas:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.recetas_manager = RecetasManager(db_connection)
        self.productos_manager = Productos(db_connection)

    def registrar_venta(self, receta_vendida_id: int, cantidad_vendida: int, precio_venta: Decimal, cliente_nombre: str = None, cliente_notas: str = None) -> int:
        """
        Registra la venta de un producto final (receta), consumiendo sus materias primas.
        """
        # Validaciones iniciales de entrada
        if not isinstance(receta_vendida_id, int) or receta_vendida_id <= 0:
            raise ValueError("El ID de la receta vendida debe ser un entero positivo.")
        if not isinstance(cantidad_vendida, int) or cantidad_vendida <= 0:
            raise ValueError("La cantidad vendida debe ser un entero positivo.")
        if not isinstance(precio_venta, Decimal) or precio_venta <= Decimal('0'):
            raise ValueError("El precio de venta debe ser un número decimal positivo.")
        
        # Iniciar la transacción
        self.db_connection.get_connection() # Asegurarse de que la conexión esté activa
        try:
            self.db_connection.commit() # Limpiar cualquier transacción pendiente
        except Error:
            self.db_connection.rollback() # Si hay una transacción pendiente, revertirla

        try:
            self.db_connection.get_connection().start_transaction() # Iniciar la transacción explícitamente

            # Convertir receta_vendida_id a entero si viene como "ID - Nombre"
            if isinstance(receta_vendida_id, str) and ' - ' in receta_vendida_id:
                receta_vendida_id = int(receta_vendida_id.split(' - ')[0])

            # Obtener los ingredientes de la receta vendida
            ingredientes_receta = self.recetas_manager.obtener_ingredientes_de_receta(receta_vendida_id)
            if not ingredientes_receta:
                raise ValueError(f"La receta ID {receta_vendida_id} no tiene ingredientes definidos. No se puede vender.")
            
            # Para cada ingrediente en la receta, decrementar el stock de MATERIAS PRIMAS
            for ingrediente in ingredientes_receta:
                ingrediente_id = ingrediente['ingrediente_id']
                cantidad_necesaria_por_unidad_final = Decimal(str(ingrediente['cantidad']))
                
                cantidad_total_a_consumir = cantidad_necesaria_por_unidad_final * Decimal(str(cantidad_vendida))
                
                # Decrementar el stock de la materia prima
                self.productos_manager.decrementar_stock(ingrediente_id, cantidad_total_a_consumir)

            # Registrar la venta en la base de datos
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            query = """
                INSERT INTO ventas (producto_id, cantidad_vendida, precio_venta, cliente_nombre, cliente_notas, fecha_venta)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (receta_vendida_id, cantidad_vendida, precio_venta, cliente_nombre, cliente_notas, fecha_actual)
            self.db_connection.execute_query(query, params)

            self.db_connection.commit() # Confirmar la transacción completa
            return self.db_connection.cursor.lastrowid

        except Error as e:
            self.db_connection.rollback() # Revertir si hay algún error de DB
            raise Exception(f"Error de base de datos al registrar venta: {str(e)}") # Relanzar como excepción general
        except ValueError as e:
            self.db_connection.rollback() # Revertir si hay algún error de validación
            raise ValueError(f"Error de validación al registrar venta: {str(e)}") # Relanzar como ValueError
        except Exception as e:
            self.db_connection.rollback() # Revertir para cualquier otro error inesperado
            raise Exception(f"Error inesperado al registrar venta: {str(e)}")

    def obtener_ventas_por_producto(self) -> list:
        """Obtiene el reporte de ventas por producto."""
        try:
            query = """
                SELECT r.nombre, SUM(v.cantidad_vendida) as total_vendido, SUM(v.precio_venta * v.cantidad_vendida) as total_ingresos
                FROM ventas v
                JOIN recetas r ON v.producto_id = r.id
                GROUP BY r.id
                ORDER BY total_ingresos DESC
            """
            return self.db_connection.fetch_all(query)
        except Error as e:
            # print(f"Error al obtener ventas por producto: {e}")
            raise e # Relanzar la excepción

    def obtener_clientes_top(self) -> list:
        """Obtiene el reporte de los clientes que más han comprado."""
        try:
            query = """
                SELECT v.cliente_nombre, COUNT(v.id) as total_compras, SUM(v.precio_venta * v.cantidad_vendida) as total_gastado
                FROM ventas v
                WHERE v.cliente_nombre IS NOT NULL AND v.cliente_nombre != ''
                GROUP BY v.cliente_nombre
                ORDER BY total_gastado DESC
                LIMIT 10
            """
            return self.db_connection.fetch_all(query)
        except Error as e:
            # print(f"Error al obtener clientes top: {e}")
            raise e # Relanzar la excepción

    def obtener_productos_bajo_stock(self) -> list:
        """Obtiene el reporte de productos que están por debajo del stock mínimo."""
        try:
            query = """
                SELECT nombre_producto, stock_minimo, cantidad
                FROM productos
                WHERE cantidad < stock_minimo
                ORDER BY nombre_producto
            """
            return self.db_connection.fetch_all(query)
        except Error as e:
            # print(f"Error al obtener productos bajo stock: {e}")
            raise e # Relanzar la excepción
