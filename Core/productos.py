import mysql.connector
from mysql.connector import Error
from decimal import Decimal
import logging
from Core.common import get_logger, logged_method, log_database_operation

class Productos:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.logger = get_logger(__name__)
        self.logger.info("📦 Productos manager inicializado")

    def agregar_producto(self, nombre_producto: str, unidad: str, stock_minimo: Decimal = Decimal('0.0000'), notas: str = None, unidad_display: str = None, proveedor: str = None) -> int:
        """
        Agrega un nuevo producto a la base de datos.
        Este método es para agregar un producto de forma independiente, no como parte de una compra.
        """
        self.logger.debug(f"🔄 Iniciando agregar_producto - nombre: '{nombre_producto}', unidad: '{unidad}', stock_minimo: {stock_minimo}, notas: {notas}, unidad_display: {unidad_display}, proveedor: {proveedor}")
        
        # Validaciones
        if not nombre_producto or not isinstance(nombre_producto, str):
            self.logger.error(f"❌ Validación fallida: nombre_producto inválido - {nombre_producto}")
            raise ValueError("El nombre del producto no puede estar vacío y debe ser una cadena de texto.")
        if not unidad or not isinstance(unidad, str):
            self.logger.error(f"❌ Validación fallida: unidad inválida - {unidad}")
            raise ValueError("La unidad base del producto no puede estar vacía y debe ser una cadena de texto.")
        if not isinstance(stock_minimo, Decimal) or stock_minimo < Decimal('0'):
            self.logger.error(f"❌ Validación fallida: stock_minimo inválido - {stock_minimo}")
            raise ValueError("El stock mínimo debe ser un número decimal no negativo.")
        if unidad_display is None:
            unidad_display = unidad
            self.logger.debug(f"ℹ️ unidad_display no proporcionada, usando unidad base: '{unidad_display}'")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            self.logger.debug(f"🔍 Verificando si el producto '{nombre_producto}' ya existe...")
            existing_product = self.obtener_producto_por_nombre(nombre_producto)
            if existing_product:
                self.logger.warning(f"⚠️ Producto '{nombre_producto}' ya existe - ID: {existing_product[0]}")
                raise ValueError(f"El producto '{nombre_producto}' ya existe en el inventario.")

            query = """
                INSERT INTO productos (nombre_producto, cantidad, unidad, total_invertido, stock_minimo, notas, unidad_display, proveedor)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor = conn.cursor()
            self.logger.debug(f"📋 Ejecutando INSERT: nombre='{nombre_producto}', cantidad=0.0000, unidad='{unidad}', total_invertido=0.00, stock_minimo={stock_minimo}, notas={notas}, unidad_display='{unidad_display}', proveedor={proveedor}")
            cursor.execute(query, (nombre_producto, Decimal('0.0000'), unidad, Decimal('0.00'), stock_minimo, notas, unidad_display, proveedor))
            
            producto_id = cursor.lastrowid
            self.logger.info(f"✅ Producto agregado exitosamente - ID: {producto_id}, nombre: '{nombre_producto}'")
            return producto_id
            
        except Error as e:
            self.logger.error(f"💥 Error al agregar producto '{nombre_producto}': {e}", exc_info=True)
            raise e
        finally:
            if cursor: 
                cursor.close()
                self.logger.debug("🔒 Cursor cerrado")

    def obtener_producto(self, producto_id: int) -> tuple:
        """Obtiene los datos de un producto por su ID."""
        self.logger.debug(f"🔍 Buscando producto por ID: {producto_id}")
        
        if not isinstance(producto_id, int) or producto_id <= 0:
            self.logger.error(f"❌ ID de producto inválido: {producto_id}")
            raise ValueError("El ID del producto debe ser un número entero positivo.")
        
        try:
            result = self.db_connection.fetch_one("""
                SELECT id, nombre_producto, cantidad, unidad, total_invertido, notas, stock_minimo, unidad_display, proveedor 
                FROM productos WHERE id = %s
            """, (producto_id,))
            
            if result:
                self.logger.debug(f"✅ Producto encontrado - ID: {result[0]}, nombre: '{result[1]}', cantidad: {result[2]} {result[3]}")
            else:
                self.logger.warning(f"⚠️ Producto no encontrado - ID: {producto_id}")
                
            return result
            
        except Exception as e:
            self.logger.error(f"💥 Error al obtener producto ID {producto_id}: {e}", exc_info=True)
            raise

    def obtener_todos_los_productos(self) -> list:
        """Obtiene todos los productos registrados."""
        self.logger.debug("📋 Obteniendo todos los productos registrados")
        
        try:
            result = self.db_connection.fetch_all(
                "SELECT id, nombre_producto, cantidad, unidad, total_invertido, notas, stock_minimo, unidad_display, proveedor FROM productos ORDER BY nombre_producto"
            )
            
            self.logger.debug(f"✅ Se encontraron {len(result)} productos")
            if self.logger.isEnabledFor(logging.DEBUG) and result:
                for producto in result[:3]:  # Mostrar primeros 3 productos
                    self.logger.debug(f"   📦 ID: {producto[0]}, nombre: '{producto[1]}', cantidad: {producto[2]} {producto[3]}")
                if len(result) > 3:
                    self.logger.debug(f"   ... y {len(result) - 3} productos más")
                    
            return result
            
        except Exception as e:
            self.logger.error(f"💥 Error al obtener todos los productos: {e}", exc_info=True)
            raise

    def obtener_productos(self) -> list:
        """Devuelve una lista de productos formateada para Combobox (ID - Nombre)."""
        self.logger.debug("📝 Formateando lista de productos para Combobox")
        
        try:
            productos_data = self.obtener_todos_los_productos()
            formatted_products = [f"{p[0]} - {p[1]}" for p in productos_data]
            
            self.logger.debug(f"✅ Formateados {len(formatted_products)} productos para Combobox")
            if self.logger.isEnabledFor(logging.DEBUG) and formatted_products:
                for product_str in formatted_products[:5]:  # Mostrar primeros 5
                    self.logger.debug(f"   🏷️ {product_str}")
                if len(formatted_products) > 5:
                    self.logger.debug(f"   ... y {len(formatted_products) - 5} productos más")
                    
            return formatted_products
            
        except Exception as e:
            self.logger.error(f"💥 Error al formatear lista de productos: {e}", exc_info=True)
            raise

    def obtener_producto_id_por_nombre(self, nombre_producto: str) -> int:
        """Obtiene el ID de un producto por su nombre (insensible a mayúsculas)."""
        self.logger.debug(f"🔍 Buscando ID de producto por nombre: '{nombre_producto}'")
        
        if not nombre_producto or not isinstance(nombre_producto, str):
            self.logger.error(f"❌ Nombre de producto inválido: {nombre_producto}")
            raise ValueError("El nombre del producto no puede estar vacío y debe ser una cadena de texto.")
        
        try:
            result = self.db_connection.fetch_one(
                "SELECT id FROM productos WHERE LOWER(nombre_producto) = LOWER(%s)", 
                (nombre_producto,)
            )
            
            if result:
                producto_id = result[0]
                self.logger.debug(f"✅ Producto encontrado - nombre: '{nombre_producto}' → ID: {producto_id}")
                return producto_id
            else:
                self.logger.warning(f"⚠️ Producto no encontrado - nombre: '{nombre_producto}'")
                return None
                
        except Exception as e:
            self.logger.error(f"💥 Error al buscar producto por nombre '{nombre_producto}': {e}", exc_info=True)
            raise

    def actualizar_stock_y_costo(self, producto_id: int, cantidad_adicional: Decimal, costo_adicional: Decimal) -> bool:
        """
        Actualiza el stock y el total invertido de un producto.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        self.logger.debug(f"🔄 Iniciando actualizar_stock_y_costo - producto_id: {producto_id}, cantidad_adicional: {cantidad_adicional}, costo_adicional: {costo_adicional}")
        
        # Validaciones
        if not isinstance(cantidad_adicional, Decimal) or cantidad_adicional < Decimal('0'):
            self.logger.error(f"❌ Validación fallida: cantidad_adicional inválida - {cantidad_adicional}")
            raise ValueError("La cantidad adicional debe ser un número decimal no negativo.")
        if not isinstance(costo_adicional, Decimal) or costo_adicional < Decimal('0'):
            self.logger.error(f"❌ Validación fallida: costo_adicional inválido - {costo_adicional}")
            raise ValueError("El costo adicional debe ser un número decimal no negativo.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            self.logger.debug(f"🔒 Bloqueando fila con FOR UPDATE para producto ID: {producto_id}")
            query_select_for_update = "SELECT cantidad, total_invertido FROM productos WHERE id = %s FOR UPDATE"
            cursor = conn.cursor()
            cursor.execute(query_select_for_update, (producto_id,))
            result = cursor.fetchone()
            
            if not result:
                self.logger.error(f"❌ Producto no encontrado para actualización - ID: {producto_id}")
                raise ValueError(f"Producto con ID {producto_id} no encontrado para actualización de stock y costo.")

            stock_actual = Decimal(str(result[0]))
            total_invertido_actual = Decimal(str(result[1]))
            
            self.logger.debug(f"📊 Valores actuales - stock: {stock_actual}, total_invertido: {total_invertido_actual}")
            
            nueva_cantidad = stock_actual + cantidad_adicional
            nuevo_total_invertido = total_invertido_actual + costo_adicional
            
            self.logger.debug(f"📈 Nuevos valores - stock: {nueva_cantidad}, total_invertido: {nuevo_total_invertido}")

            query_update = """
                UPDATE productos
                SET cantidad = %s, total_invertido = %s
                WHERE id = %s
            """
            self.logger.debug(f"📋 Ejecutando UPDATE: cantidad={nueva_cantidad}, total_invertido={nuevo_total_invertido}, id={producto_id}")
            cursor.execute(query_update, (nueva_cantidad, nuevo_total_invertido, producto_id))
            return True
        except Error as e:
            self.logger.error(f"💥 Error al actualizar stock y costo del producto {producto_id}: {e}", exc_info=True)
            raise e
        finally:
            if cursor: cursor.close()

    def agregar_o_actualizar_producto(self, nombre_producto: str, cantidad_compra: Decimal, unidad_interna_base: str, 
                                      precio_unitario_compra_por_unidad_interna_base: Decimal, stock_minimo: Decimal, 
                                      unidad_display: str, proveedor: str = None) -> int:
        """
        Agrega un producto si no existe, o actualiza su stock y total invertido si ya existe.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        self.logger.debug(f"🔄 Iniciando agregar_o_actualizar_producto")
        self.logger.debug(f"   📋 Parámetros recibidos:")
        self.logger.debug(f"      - nombre_producto: '{nombre_producto}'")
        self.logger.debug(f"      - cantidad_compra: {cantidad_compra}")
        self.logger.debug(f"      - unidad_interna_base: '{unidad_interna_base}'")
        self.logger.debug(f"      - precio_unitario_compra_por_unidad_interna_base: {precio_unitario_compra_por_unidad_interna_base}")
        self.logger.debug(f"      - stock_minimo: {stock_minimo}")
        self.logger.debug(f"      - unidad_display: '{unidad_display}'")
        self.logger.debug(f"      - proveedor: {proveedor}")

        # Validaciones con logging detallado
        self.logger.debug("🔍 Validando parámetros...")
        if not nombre_producto or not isinstance(nombre_producto, str):
            self.logger.error(f"❌ Validación fallida: nombre_producto inválido - {nombre_producto}")
            raise ValueError("El nombre del producto no puede estar vacío y debe ser una cadena de texto.")
        if not isinstance(cantidad_compra, Decimal) or cantidad_compra < Decimal('0'):
            self.logger.error(f"❌ Validación fallida: cantidad_compra inválida - {cantidad_compra}")
            raise ValueError("La cantidad de compra debe ser un número decimal no negativo.")
        if not unidad_interna_base or not isinstance(unidad_interna_base, str):
            self.logger.error(f"❌ Validación fallida: unidad_interna_base inválida - {unidad_interna_base}")
            raise ValueError("La unidad interna base no puede estar vacía y debe ser una cadena de texto.")
        if not isinstance(precio_unitario_compra_por_unidad_interna_base, Decimal) or precio_unitario_compra_por_unidad_interna_base < Decimal('0'):
            self.logger.error(f"❌ Validación fallida: precio_unitario_compra_por_unidad_interna_base inválido - {precio_unitario_compra_por_unidad_interna_base}")
            raise ValueError("El precio unitario de compra debe ser un número decimal no negativo.")
        if not isinstance(stock_minimo, Decimal) or stock_minimo < Decimal('0'):
            self.logger.error(f"❌ Validación fallida: stock_minimo inválido - {stock_minimo}")
            raise ValueError("El stock mínimo debe ser un número decimal no negativo.")
        if not unidad_display or not isinstance(unidad_display, str):
            self.logger.error(f"❌ Validación fallida: unidad_display inválida - {unidad_display}")
            raise ValueError("La unidad de visualización no puede estar vacía y debe ser una cadena de texto.")
        
        self.logger.debug("✅ Todas las validaciones pasaron")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            self.logger.debug(f"🔍 Buscando producto existente con nombre: '{nombre_producto}'")
            cursor = conn.cursor()
            cursor.execute("SELECT id, cantidad, total_invertido, unidad, stock_minimo, unidad_display, proveedor FROM productos WHERE LOWER(nombre_producto) = LOWER(%s) FOR UPDATE", (nombre_producto,))
            producto_existente = cursor.fetchone()

            costo_compra_actual = cantidad_compra * precio_unitario_compra_por_unidad_interna_base
            self.logger.debug(f"💰 Costo de compra calculado: {cantidad_compra} × {precio_unitario_compra_por_unidad_interna_base} = {costo_compra_actual}")

            if producto_existente:
                self.logger.debug("✅ Producto existente encontrado")
                self.logger.debug(f"   📊 Datos actuales del producto:")
                self.logger.debug(f"      - ID: {producto_existente[0]}")
                self.logger.debug(f"      - Stock actual: {producto_existente[1]} {producto_existente[3]}")
                self.logger.debug(f"      - Total invertido actual: ${producto_existente[2]}")
                self.logger.debug(f"      - Stock mínimo actual: {producto_existente[4]}")
                self.logger.debug(f"      - Unidad display actual: '{producto_existente[5]}'")
                self.logger.debug(f"      - Proveedor actual: {producto_existente[6]}")

                producto_id = producto_existente[0]
                stock_actual = Decimal(str(producto_existente[1]))
                total_invertido_actual = Decimal(str(producto_existente[2]))
                
                nueva_cantidad = stock_actual + cantidad_compra
                nuevo_total_invertido = total_invertido_actual + costo_compra_actual
                
                self.logger.debug(f"📈 Actualizando producto existente:")
                self.logger.debug(f"   - Nueva cantidad: {stock_actual} + {cantidad_compra} = {nueva_cantidad}")
                self.logger.debug(f"   - Nuevo total invertido: ${total_invertido_actual} + ${costo_compra_actual} = ${nuevo_total_invertido}")

                query_update = """
                    UPDATE productos
                    SET cantidad = %s, total_invertido = %s, unidad = %s, stock_minimo = %s, unidad_display = %s, proveedor = %s
                    WHERE id = %s
                """
                self.logger.debug(f"📋 Ejecutando UPDATE con parámetros:")
                self.logger.debug(f"   - cantidad: {nueva_cantidad}")
                self.logger.debug(f"   - total_invertido: {nuevo_total_invertido}")
                self.logger.debug(f"   - unidad: {unidad_interna_base}")
                self.logger.debug(f"   - stock_minimo: {stock_minimo}")
                self.logger.debug(f"   - unidad_display: {unidad_display}")
                self.logger.debug(f"   - proveedor: {proveedor}")
                self.logger.debug(f"   - id: {producto_id}")
                
                cursor.execute(query_update, (nueva_cantidad, nuevo_total_invertido, unidad_interna_base, stock_minimo, unidad_display, proveedor, producto_id))
                self.logger.info(f"✅ Producto actualizado exitosamente - ID: {producto_id}, nombre: '{nombre_producto}'")
                return producto_id
            else:
                self.logger.debug("🆕 Producto no existe, creando nuevo registro")
                query_insert = """
                    INSERT INTO productos (nombre_producto, cantidad, unidad, total_invertido, stock_minimo, unidad_display, proveedor)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                self.logger.debug(f"📋 Ejecutando INSERT con parámetros:")
                self.logger.debug(f"   - nombre_producto: '{nombre_producto}'")
                self.logger.debug(f"   - cantidad: {cantidad_compra}")
                self.logger.debug(f"   - unidad: '{unidad_interna_base}'")
                self.logger.debug(f"   - total_invertido: {costo_compra_actual}")
                self.logger.debug(f"   - stock_minimo: {stock_minimo}")
                self.logger.debug(f"   - unidad_display: '{unidad_display}'")
                self.logger.debug(f"   - proveedor: {proveedor}")
                
                cursor.execute(query_insert, (nombre_producto, cantidad_compra, unidad_interna_base, costo_compra_actual, stock_minimo, unidad_display, proveedor))
                producto_id = cursor.lastrowid
                self.logger.info(f"✅ Producto creado exitosamente - ID: {producto_id}, nombre: '{nombre_producto}'")
                return producto_id
        except Error as e:
            self.logger.error(f"💥 Error en agregar_o_actualizar_producto: {e}", exc_info=True)
            raise e
        finally:
            if cursor: 
                cursor.close()
                self.logger.debug("🔒 Cursor cerrado")

    def actualizar_stock_minimo(self, producto_id: int, nuevo_stock_minimo: Decimal) -> bool:
        """
        Actualiza el stock mínimo de un producto.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        self.logger.debug(f"🔄 Iniciando actualizar_stock_minimo")
        self.logger.debug(f"   📋 Parámetros recibidos:")
        self.logger.debug(f"      - producto_id: {producto_id}")
        self.logger.debug(f"      - nuevo_stock_minimo: {nuevo_stock_minimo}")

        # Validaciones con logging detallado
        self.logger.debug("🔍 Validando parámetros...")
        if not isinstance(producto_id, int) or producto_id <= 0:
            self.logger.error(f"❌ Validación fallida: producto_id inválido - {producto_id}")
            raise ValueError("El ID del producto debe ser un número entero positivo.")
        if not isinstance(nuevo_stock_minimo, Decimal) or nuevo_stock_minimo < Decimal('0'):
            self.logger.error(f"❌ Validación fallida: nuevo_stock_minimo inválido - {nuevo_stock_minimo}")
            raise ValueError("El stock mínimo debe ser un número decimal no negativo.")
        
        self.logger.debug("✅ Todas las validaciones pasaron")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            # Verificar si el producto existe
            self.logger.debug(f"🔍 Verificando existencia del producto ID: {producto_id}")
            if not self.existe_producto(producto_id):
                self.logger.error(f"❌ Producto no encontrado - ID: {producto_id}")
                raise ValueError(f"Producto con ID {producto_id} no encontrado.")

            # Obtener información actual para logging
            self.logger.debug(f"📊 Obteniendo información actual del producto ID: {producto_id}")
            producto_actual = self.obtener_producto(producto_id)
            if producto_actual:
                stock_minimo_actual = producto_actual[6]  # Índice 6 es stock_minimo
                self.logger.debug(f"   📋 Datos actuales:")
                self.logger.debug(f"      - Nombre: '{producto_actual[1]}'")
                self.logger.debug(f"      - Stock mínimo actual: {stock_minimo_actual}")
                self.logger.debug(f"      - Stock actual: {producto_actual[2]} {producto_actual[3]}")

            cursor = conn.cursor()
            query = "UPDATE productos SET stock_minimo = %s WHERE id = %s"
            self.logger.debug(f"📋 Ejecutando UPDATE:")
            self.logger.debug(f"   - stock_minimo: {nuevo_stock_minimo}")
            self.logger.debug(f"   - id: {producto_id}")
            
            cursor.execute(query, (nuevo_stock_minimo, producto_id))
            
            if cursor.rowcount > 0:
                self.logger.info(f"✅ Stock mínimo actualizado exitosamente - ID: {producto_id}, nuevo_stock_minimo: {nuevo_stock_minimo}")
                return True
            else:
                self.logger.warning(f"⚠️ No se actualizó ningún registro - ID: {producto_id}")
                return False
                
        except Error as e:
            self.logger.error(f"💥 Error al actualizar stock mínimo del producto {producto_id}: {e}", exc_info=True)
            raise e
        finally:
            if cursor: 
                cursor.close()
                self.logger.debug("🔒 Cursor cerrado")

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


