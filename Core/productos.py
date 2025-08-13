import mysql.connector
from mysql.connector import Error
from decimal import Decimal

class Productos:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def agregar_producto(self, nombre_producto: str, unidad: str, stock_minimo: Decimal = Decimal('0.0000'), notas: str = None, unidad_display: str = None, proveedor: str = None) -> int:
        """
        Agrega un nuevo producto a la base de datos.
        Este método es para agregar un producto de forma independiente, no como parte de una compra.
        """
        if not nombre_producto or not isinstance(nombre_producto, str):
            raise ValueError("El nombre del producto no puede estar vacío y debe ser una cadena de texto.")
        if not unidad or not isinstance(unidad, str):
            raise ValueError("La unidad base del producto no puede estar vacía y debe ser una cadena de texto.")
        if not isinstance(stock_minimo, Decimal) or stock_minimo < Decimal('0'):
            raise ValueError("El stock mínimo debe ser un número decimal no negativo.")
        if unidad_display is None: # Si no se especifica, usa la unidad base
            unidad_display = unidad

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            # Verificar si el producto ya existe (insensible a mayúsculas)
            existing_product = self.obtener_producto_por_nombre(nombre_producto)
            if existing_product:
                raise ValueError(f"El producto '{nombre_producto}' ya existe en el inventario.")

            query = """
                INSERT INTO productos (nombre_producto, cantidad, unidad, total_invertido, stock_minimo, notas, unidad_display, proveedor)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor = conn.cursor()
            cursor.execute(query, (nombre_producto, Decimal('0.0000'), unidad, Decimal('0.00'), stock_minimo, notas, unidad_display, proveedor))
            # No commit aquí, se espera que el llamador maneje la transacción si es parte de una mayor.
            # Si se llama directamente, el llamador debe hacer commit.
            return cursor.lastrowid
        except Error as e:
            # print(f"Error al agregar producto: {e}") # Para depuración
            raise e # Relanzar la excepción
        finally:
            if cursor: cursor.close()

    def obtener_producto(self, producto_id: int) -> tuple:
        """Obtiene los datos de un producto por su ID."""
        # No es necesario obtener la conexión y el cursor manualmente si usamos fetch_one
        return self.db_connection.fetch_one("""
            SELECT id, nombre_producto, cantidad, unidad, total_invertido, notas, stock_minimo, unidad_display, proveedor 
            FROM productos WHERE id = %s
        """, (producto_id,))

    def obtener_todos_los_productos(self) -> list:
        """Obtiene todos los productos registrados."""
        # No es necesario obtener la conexión y el cursor manualmente si usamos fetch_all
        return self.db_connection.fetch_all("SELECT id, nombre_producto, cantidad, unidad, total_invertido, notas, stock_minimo, unidad_display, proveedor FROM productos ORDER BY nombre_producto")

    def obtener_productos(self) -> list:
        """Devuelve una lista de productos formateada para Combobox (ID - Nombre)."""
        productos_data = self.obtener_todos_los_productos()
        return [f"{p[0]} - {p[1]}" for p in productos_data]

    def obtener_producto_id_por_nombre(self, nombre_producto: str) -> int:
        """Obtiene el ID de un producto por su nombre (insensible a mayúsculas)."""
        result = self.db_connection.fetch_one("SELECT id FROM productos WHERE LOWER(nombre_producto) = LOWER(%s)", (nombre_producto,))
        return result[0] if result else None

    def actualizar_stock_y_costo(self, producto_id: int, cantidad_adicional: Decimal, costo_adicional: Decimal) -> bool:
        """
        Actualiza el stock y el total invertido de un producto.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not isinstance(cantidad_adicional, Decimal) or cantidad_adicional < Decimal('0'):
            raise ValueError("La cantidad adicional debe ser un número decimal no negativo.")
        if not isinstance(costo_adicional, Decimal) or costo_adicional < Decimal('0'):
            raise ValueError("El costo adicional debe ser un número decimal no negativo.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            # Usar FOR UPDATE para bloquear la fila durante la actualización
            query_select_for_update = "SELECT cantidad, total_invertido FROM productos WHERE id = %s FOR UPDATE"
            cursor = conn.cursor()
            cursor.execute(query_select_for_update, (producto_id,))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Producto con ID {producto_id} no encontrado para actualización de stock y costo.")

            stock_actual, total_invertido_actual = Decimal(str(result[0])), Decimal(str(result[1]))
            
            nueva_cantidad = stock_actual + cantidad_adicional
            nuevo_total_invertido = total_invertido_actual + costo_adicional

            query_update = """
                UPDATE productos
                SET cantidad = %s, total_invertido = %s
                WHERE id = %s
            """
            cursor.execute(query_update, (nueva_cantidad, nuevo_total_invertido, producto_id))
            return True
        except Error as e:
            # print(f"Error al actualizar stock y costo del producto {producto_id}: {e}")
            raise e # Relanzar la excepción
        finally:
            if cursor: cursor.close()

    def agregar_o_actualizar_producto(self, nombre_producto: str, cantidad_compra: Decimal, unidad_interna_base: str, 
                                      precio_unitario_compra_por_unidad_interna_base: Decimal, stock_minimo: Decimal, 
                                      unidad_display: str, proveedor: str = None) -> int:
        """
        Agrega un producto si no existe, o actualiza su stock y total invertido si ya existe.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not nombre_producto or not isinstance(nombre_producto, str):
            raise ValueError("El nombre del producto no puede estar vacío y debe ser una cadena de texto.")
        if not isinstance(cantidad_compra, Decimal) or cantidad_compra < Decimal('0'):
            raise ValueError("La cantidad de compra debe ser un número decimal no negativo.")
        if not unidad_interna_base or not isinstance(unidad_interna_base, str):
            raise ValueError("La unidad interna base no puede estar vacía y debe ser una cadena de texto.")
        if not isinstance(precio_unitario_compra_por_unidad_interna_base, Decimal) or precio_unitario_compra_por_unidad_interna_base < Decimal('0'):
            raise ValueError("El precio unitario de compra debe ser un número decimal no negativo.")
        if not isinstance(stock_minimo, Decimal) or stock_minimo < Decimal('0'):
            raise ValueError("El stock mínimo debe ser un número decimal no negativo.")
        if not unidad_display or not isinstance(unidad_display, str):
            raise ValueError("La unidad de visualización no puede estar vacía y debe ser una cadena de texto.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            # Usamos LOWER() para hacer la búsqueda insensible a mayúsculas y FOR UPDATE para bloquear
            cursor.execute("SELECT id, cantidad, total_invertido, unidad, stock_minimo, unidad_display, proveedor FROM productos WHERE LOWER(nombre_producto) = LOWER(%s) FOR UPDATE", (nombre_producto,))
            producto_existente = cursor.fetchone()

            costo_compra_actual = cantidad_compra * precio_unitario_compra_por_unidad_interna_base

            if producto_existente:
                producto_id = producto_existente[0]
                stock_actual = Decimal(str(producto_existente[1]))
                total_invertido_actual = Decimal(str(producto_existente[2]))
                
                # Actualizar solo si los valores son diferentes o si se fuerza la actualización
                # Mantener la unidad base y display existentes a menos que se especifique lo contrario
                # (aunque en compras, la unidad_interna_base y unidad_display vienen del cálculo)
                unidad_base_existente = producto_existente[3]
                stock_minimo_existente = producto_existente[4]
                unidad_display_existente = producto_existente[5]
                proveedor_existente = producto_existente[6]

                nueva_cantidad = stock_actual + cantidad_compra
                nuevo_total_invertido = total_invertido_actual + costo_compra_actual

                query_update = """
                    UPDATE productos
                    SET cantidad = %s, total_invertido = %s, unidad = %s, stock_minimo = %s, unidad_display = %s, proveedor = %s
                    WHERE id = %s
                """
                cursor.execute(query_update, (nueva_cantidad, nuevo_total_invertido, unidad_interna_base, stock_minimo, unidad_display, proveedor, producto_id))
                return producto_id
            else:
                query_insert = """
                    INSERT INTO productos (nombre_producto, cantidad, unidad, total_invertido, stock_minimo, unidad_display, proveedor)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query_insert, (nombre_producto, cantidad_compra, unidad_interna_base, costo_compra_actual, stock_minimo, unidad_display, proveedor))
                return cursor.lastrowid
        except Error as e:
            # print(f"Error en agregar_o_actualizar_producto: {e}")
            raise e
        finally:
            if cursor: cursor.close()

    def actualizar_stock_minimo(self, producto_id: int, nuevo_stock_minimo: Decimal) -> bool:
        """
        Actualiza el stock mínimo de un producto.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not isinstance(nuevo_stock_minimo, Decimal) or nuevo_stock_minimo < Decimal('0'):
            raise ValueError("El stock mínimo debe ser un número decimal no negativo.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            query = "UPDATE productos SET stock_minimo = %s WHERE id = %s"
            cursor.execute(query, (nuevo_stock_minimo, producto_id))
            return True
        except Error as e:
            # print(f"Error al actualizar stock mínimo del producto {producto_id}: {e}")
            raise e
        finally:
            if cursor: cursor.close()

    def incrementar_stock(self, producto_id: int, cantidad_a_incrementar: Decimal) -> bool:
        """
        Incrementa el stock de un producto.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not isinstance(cantidad_a_incrementar, Decimal) or cantidad_a_incrementar < Decimal('0'):
            raise ValueError("La cantidad a incrementar debe ser un número decimal no negativo.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            if isinstance(producto_id, str) and ' - ' in producto_id:
                producto_id = int(producto_id.split(' - ')[0])

            cursor = conn.cursor()
            cursor.execute("SELECT cantidad FROM productos WHERE id = %s FOR UPDATE", (producto_id,))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Producto con ID {producto_id} no encontrado.")
            stock_actual = Decimal(str(result[0]))

            nueva_cantidad = stock_actual + cantidad_a_incrementar
            cursor.execute("UPDATE productos SET cantidad = %s WHERE id = %s", (nueva_cantidad, producto_id))
            return True
        except Error as e:
            # print(f"Error al incrementar stock del producto {producto_id}: {e}")
            raise e
        finally:
            if cursor: cursor.close()

    def decrementar_stock(self, producto_id: int, cantidad_a_decrementar: Decimal) -> bool:
        """
        Decrementa el stock de un producto y ajusta el total invertido proporcionalmente.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not isinstance(cantidad_a_decrementar, Decimal) or cantidad_a_decrementar < Decimal('0'):
            raise ValueError("La cantidad a decrementar debe ser un número decimal no negativo.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            if isinstance(producto_id, str) and ' - ' in producto_id:
                producto_id = int(producto_id.split(' - ')[0])

            cursor = conn.cursor()
            # Obtener cantidad y total_invertido para calcular el costo promedio actual
            cursor.execute("SELECT cantidad, total_invertido FROM productos WHERE id = %s FOR UPDATE", (producto_id,))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Producto con ID {producto_id} no encontrado.")
            
            stock_actual = Decimal(str(result[0]))
            total_invertido_actual = Decimal(str(result[1]))

            if stock_actual < cantidad_a_decrementar:
                raise ValueError(f"Stock insuficiente para el producto {producto_id}. Disponible: {stock_actual:.4f}, Requerido: {cantidad_a_decrementar:.4f}")

            # Calcular el costo promedio por unidad antes de la reducción
            costo_promedio_por_unidad = Decimal('0.00')
            if stock_actual > Decimal('0'):
                costo_promedio_por_unidad = total_invertido_actual / stock_actual
            
            # Calcular el nuevo total invertido
            nuevo_total_invertido = total_invertido_actual - (cantidad_a_decrementar * costo_promedio_por_unidad)
            # Asegurarse de que total_invertido no sea negativo (puede ocurrir por pequeñas imprecisiones de Decimal si el stock es muy bajo)
            if nuevo_total_invertido < Decimal('0'):
                nuevo_total_invertido = Decimal('0')

            nueva_cantidad = stock_actual - cantidad_a_decrementar
            
            query_update = """
                UPDATE productos
                SET cantidad = %s, total_invertido = %s
                WHERE id = %s
            """
            cursor.execute(query_update, (nueva_cantidad, nuevo_total_invertido, producto_id))
            return True
        except Error as e:
            # print(f"Error al decrementar stock del producto {producto_id}: {e}")
            raise e
        finally:
            if cursor: cursor.close()

    def obtener_costo_promedio(self, producto_id: int) -> Decimal:
        """Obtiene el costo promedio por unidad de un producto."""
        conn = self.db_connection.get_connection()
        cursor = None
        try:
            if isinstance(producto_id, str) and ' - ' in producto_id:
                producto_id = int(producto_id.split(' - ')[0])

            cursor = conn.cursor()
            cursor.execute("SELECT cantidad, total_invertido FROM productos WHERE id = %s", (producto_id,))
            result = cursor.fetchone()
            if result and Decimal(str(result[0])) > Decimal('0'):
                return Decimal(str(result[1])) / Decimal(str(result[0]))
            return Decimal('0.00')
        except Error as e:
            # print(f"Error al obtener costo promedio del producto {producto_id}: {e}")
            raise e # Relanzar para que el llamador maneje
        finally:
            if cursor: cursor.close()

    def actualizar_unidad_display(self, producto_id: int, nueva_unidad_display: str) -> bool:
        """
        Actualiza la unidad de visualización de un producto.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not nueva_unidad_display or not isinstance(nueva_unidad_display, str):
            raise ValueError("La nueva unidad de visualización no puede estar vacía y debe ser una cadena de texto.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            if isinstance(producto_id, str) and ' - ' in producto_id:
                producto_id = int(producto_id.split(' - ')[0])
            cursor = conn.cursor()
            query = """
                UPDATE productos
                SET unidad_display = %s
                WHERE id = %s
            """
            cursor.execute(query, (nueva_unidad_display, producto_id))
            return True
        except Error as e:
            # print(f"Error al actualizar unidad_display del producto {producto_id}: {e}")
            raise e
        finally:
            if cursor: cursor.close()

    def obtener_producto_por_nombre(self, nombre_producto: str) -> tuple:
        """Obtiene un producto por su nombre (insensible a mayúsculas)."""
        # Usar fetch_one para simplificar
        return self.db_connection.fetch_one(
            "SELECT id, nombre_producto, cantidad, unidad, total_invertido, notas, stock_minimo, unidad_display, proveedor "
            "FROM productos WHERE LOWER(nombre_producto) = LOWER(%s)",
            (nombre_producto,)
        )

    def obtener_nombres_productos(self) -> list:
        """Devuelve una lista de nombres de productos registrados (para el Combobox)."""
        # Usar fetch_all para simplificar
        results = self.db_connection.fetch_all("SELECT DISTINCT nombre_producto FROM productos ORDER BY nombre_producto")
        return [row[0] for row in results]

    def obtener_unidad_base(self, producto_id: int) -> str:
        """Obtiene la unidad base de un producto por su ID."""
        result = self.db_connection.fetch_one("SELECT unidad FROM productos WHERE id = %s", (producto_id,))
        if result:
            return result[0]
        raise ValueError(f"Producto con ID {producto_id} no encontrado o sin unidad base definida.")

    def existe_producto(self, producto_id: int) -> bool:
        """Verifica si un producto existe en la base de datos."""
        result = self.db_connection.fetch_one("SELECT COUNT(*) FROM productos WHERE id = %s", (producto_id,))
        return result[0] > 0

    def eliminar_producto(self, producto_id: int) -> bool:
        """
        Elimina un producto de la base de datos.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not isinstance(producto_id, int) or producto_id <= 0:
            raise ValueError("El ID del producto debe ser un número entero positivo.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            # Verificar si el producto existe
            if not self.existe_producto(producto_id):
                raise ValueError(f"Producto con ID {producto_id} no encontrado.")

            # Verificar si el producto tiene stock actual
            cursor = conn.cursor()
            cursor.execute("SELECT cantidad FROM productos WHERE id = %s", (producto_id,))
            result = cursor.fetchone()
            if result and Decimal(str(result[0])) > Decimal('0'):
                raise ValueError("No se puede eliminar un producto que tiene stock actual. Por favor, ajuste el stock a 0 antes de eliminar.")

            # Verificar si el producto está siendo utilizado en otras tablas
            # Verificar en tabla de recetas
            cursor.execute("SELECT COUNT(*) FROM recetas WHERE producto_id = %s", (producto_id,))
            if cursor.fetchone()[0] > 0:
                raise ValueError("No se puede eliminar este producto porque está siendo utilizado en recetas.")

            # Verificar en tabla de compras
            cursor.execute("SELECT COUNT(*) FROM compras WHERE producto_id = %s", (producto_id,))
            if cursor.fetchone()[0] > 0:
                raise ValueError("No se puede eliminar este producto porque tiene compras asociadas.")

            # Verificar en tabla de ventas
            cursor.execute("SELECT COUNT(*) FROM ventas WHERE producto_id = %s", (producto_id,))
            if cursor.fetchone()[0] > 0:
                raise ValueError("No se puede eliminar este producto porque tiene ventas asociadas.")

            # Verificar en tabla de producción
            cursor.execute("SELECT COUNT(*) FROM produccion WHERE producto_id = %s", (producto_id,))
            if cursor.fetchone()[0] > 0:
                raise ValueError("No se puede eliminar este producto porque está siendo utilizado en producción.")

            # Si pasa todas las verificaciones, eliminar el producto
            cursor.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
            return True
            
        except Error as e:
            # print(f"Error al eliminar producto {producto_id}: {e}")
            raise e
        finally:
            if cursor: cursor.close()

