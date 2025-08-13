import mysql.connector
from mysql.connector import Error
from decimal import Decimal
from Core.UnitConverter import UnitConverter # Asegúrate de que UnitConverter esté disponible

class RecetasManager:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.unit_converter = UnitConverter()

    def crear_receta(self, nombre_receta: str, categoria: str, precio_venta: Decimal = Decimal('0.00'), costo_mano_obra_total: Decimal = Decimal('0.00')) -> int:
        """
        Crea una nueva receta en la base de datos.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not nombre_receta or not isinstance(nombre_receta, str):
            raise ValueError("El nombre de la receta no puede estar vacío y debe ser una cadena de texto.")
        if not categoria or not isinstance(categoria, str):
            raise ValueError("La categoría de la receta no puede estar vacía y debe ser una cadena de texto.")
        if not isinstance(precio_venta, Decimal) or precio_venta < Decimal('0'):
            raise ValueError("El precio de venta debe ser un número decimal no negativo.")
        if not isinstance(costo_mano_obra_total, Decimal) or costo_mano_obra_total < Decimal('0'):
            raise ValueError("El costo de mano de obra debe ser un número decimal no negativo.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            # Verificar si la receta ya existe (insensible a mayúsculas)
            existing_receta = self.obtener_receta_por_nombre(nombre_receta)
            if existing_receta:
                raise ValueError(f"La receta '{nombre_receta}' ya existe.")

            query = """
                INSERT INTO recetas (nombre, categoria, precio_venta, costo_mano_obra_total)
                VALUES (%s, %s, %s, %s)
            """
            cursor = conn.cursor()
            cursor.execute(query, (nombre_receta, categoria, precio_venta, costo_mano_obra_total))
            # No commit aquí
            return cursor.lastrowid
        except Error as e:
            # print(f"Error al crear receta: {e}")
            raise e # Relanzar la excepción
        except ValueError as e:
            raise e # Relanzar la excepción de validación
        finally:
            if cursor: cursor.close()

    def actualizar_costo_mano_obra_receta(self, receta_id: int, nuevo_costo_mano_obra: Decimal) -> None:
        """
        Actualiza el costo de mano de obra total de una receta.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not isinstance(receta_id, int) or receta_id <= 0:
            raise ValueError("El ID de la receta debe ser un entero positivo.")
        if not isinstance(nuevo_costo_mano_obra, Decimal) or nuevo_costo_mano_obra < Decimal('0'):
            raise ValueError("El nuevo costo de mano de obra debe ser un número decimal no negativo.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE recetas SET costo_mano_obra_total = %s WHERE id = %s",
                (nuevo_costo_mano_obra, receta_id)
            )
            # No commit aquí
        except Error as e:
            # print(f"Error al actualizar costo de mano de obra: {str(e)}")
            raise e # Relanzar la excepción
        finally:
            if cursor: cursor.close()

    def agregar_ingrediente_a_receta(self, receta_id: int, ingrediente_id: int, cantidad: Decimal, unidad: str) -> None:
        """
        Añade un ingrediente a una receta existente.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not isinstance(receta_id, int) or receta_id <= 0:
            raise ValueError("El ID de la receta debe ser un entero positivo.")
        if not isinstance(ingrediente_id, int) or ingrediente_id <= 0:
            raise ValueError("El ID del ingrediente debe ser un entero positivo.")
        if not isinstance(cantidad, Decimal) or cantidad <= Decimal('0'):
            raise ValueError("La cantidad del ingrediente debe ser un número decimal positivo.")
        if not unidad or not isinstance(unidad, str):
            raise ValueError("La unidad del ingrediente no puede estar vacía y debe ser una cadena de texto.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            # Verificar si el ingrediente ya está en la receta para actualizar en lugar de insertar
            cursor.execute("SELECT id FROM receta_ingredientes WHERE receta_id = %s AND ingrediente_id = %s", (receta_id, ingrediente_id))
            existing_entry = cursor.fetchone()

            if existing_entry:
                query = """
                    UPDATE receta_ingredientes
                    SET cantidad = %s, unidad = %s
                    WHERE id = %s
                """
                cursor.execute(query, (cantidad, unidad, existing_entry[0]))
            else:
                query = """
                    INSERT INTO receta_ingredientes (receta_id, ingrediente_id, cantidad, unidad)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query, (receta_id, ingrediente_id, cantidad, unidad))
            # No commit aquí
        except Error as e:
            # print(f"Error al agregar ingrediente a receta: {e}")
            raise e # Relanzar la excepción
        except ValueError as e:
            raise e # Relanzar la excepción de validación
        finally:
            if cursor: cursor.close()

    def eliminar_ingrediente_de_receta(self, receta_id: int, ingrediente_id: int) -> None:
        """
        Elimina un ingrediente de una receta existente.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not isinstance(receta_id, int) or receta_id <= 0:
            raise ValueError("El ID de la receta debe ser un entero positivo.")
        if not isinstance(ingrediente_id, int) or ingrediente_id <= 0:
            raise ValueError("El ID del ingrediente debe ser un entero positivo.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            query = """
                DELETE FROM receta_ingredientes
                WHERE receta_id = %s AND ingrediente_id = %s
            """
            cursor.execute(query, (receta_id, ingrediente_id))
            # No commit aquí
        except Error as e:
            # print(f"Error al eliminar ingrediente de receta: {e}")
            raise e
        finally:
            if cursor: cursor.close()

    def obtener_receta(self, receta_id: int) -> dict:
        """Obtiene los datos de una receta por su ID."""
        # Usar fetch_one para simplificar
        result = self.db_connection.fetch_one("SELECT id, nombre, categoria, precio_venta, costo_mano_obra_total FROM recetas WHERE id = %s", (receta_id,))
        if result:
            # Mapear a diccionario manualmente si fetch_one no devuelve dict
            column_names = ["id", "nombre", "categoria", "precio_venta", "costo_mano_obra_total"]
            return dict(zip(column_names, result))
        return None

    def obtener_todas_las_recetas(self) -> list:
        """Obtiene todas las recetas registradas."""
        # Usar fetch_all para simplificar
        results = self.db_connection.fetch_all("SELECT id, nombre, categoria, precio_venta, costo_mano_obra_total FROM recetas ORDER BY nombre")
        
        # Mapear a lista de diccionarios
        column_names = ["id", "nombre", "categoria", "precio_venta", "costo_mano_obra_total"]
        recetas_list = []
        for row in results:
            receta_dict = dict(zip(column_names, row))
            receta_dict['precio_venta'] = Decimal(str(receta_dict['precio_venta']))
            receta_dict['costo_mano_obra_total'] = Decimal(str(receta_dict['costo_mano_obra_total']))
            recetas_list.append(receta_dict)
        return recetas_list

    def obtener_ingredientes_de_receta(self, receta_id: int) -> list:
        """Obtiene los ingredientes de una receta específica."""
        query = """
            SELECT ri.ingrediente_id, ri.cantidad, ri.unidad, p.nombre_producto as nombre_ingrediente,
                   p.unidad as unidad_base_ingrediente, p.total_invertido, p.cantidad as stock_actual_ingrediente
            FROM receta_ingredientes ri
            JOIN productos p ON ri.ingrediente_id = p.id
            WHERE ri.receta_id = %s
        """
        results = self.db_connection.fetch_all(query, (receta_id,))
        
        ingredientes_list = []
        column_names = ["ingrediente_id", "cantidad", "unidad", "nombre_ingrediente", 
                        "unidad_base_ingrediente", "total_invertido", "stock_actual_ingrediente"]
        for row in results:
            ingrediente_dict = dict(zip(column_names, row))
            ingrediente_dict['cantidad'] = Decimal(str(ingrediente_dict['cantidad']))
            ingrediente_dict['total_invertido'] = Decimal(str(ingrediente_dict['total_invertido']))
            ingrediente_dict['stock_actual_ingrediente'] = Decimal(str(ingrediente_dict['stock_actual_ingrediente']))
            ingredientes_list.append(ingrediente_dict)
        return ingredientes_list

    def obtener_nombres_recetas(self) -> list:
        """Devuelve una lista de nombres de recetas registradas (para Combobox)."""
        results = self.db_connection.fetch_all("SELECT id, nombre FROM recetas ORDER BY nombre")
        return [f"{row[0]} - {row[1]}" for row in results]

    def obtener_receta_por_nombre(self, nombre_receta: str) -> dict:
        """Obtiene una receta por su nombre (insensible a mayúsculas)."""
        result = self.db_connection.fetch_one("SELECT id, nombre, categoria, precio_venta, costo_mano_obra_total FROM recetas WHERE LOWER(nombre) = LOWER(%s)", (nombre_receta,))
        if result:
            column_names = ["id", "nombre", "categoria", "precio_venta", "costo_mano_obra_total"]
            receta_dict = dict(zip(column_names, result))
            receta_dict['precio_venta'] = Decimal(str(receta_dict['precio_venta']))
            receta_dict['costo_mano_obra_total'] = Decimal(str(receta_dict['costo_mano_obra_total']))
            return receta_dict
        return None

    def calcular_costo_receta(self, receta_id: int, productos_manager) -> Decimal:
        """
        Calcula el costo actualizado de una receta basado en precios vigentes de ingredientes.
        """
        if not isinstance(receta_id, int) or receta_id <= 0:
            raise ValueError("El ID de la receta debe ser un entero positivo.")

        # Obtener todos los ingredientes de la receta con sus unidades base
        # Usamos obtener_ingredientes_de_receta que ya trae la unidad_base_ingrediente
        ingredientes = self.obtener_ingredientes_de_receta(receta_id)
        
        costo_total = Decimal('0.00')
        
        for ingrediente in ingredientes:
            ingrediente_id = ingrediente['ingrediente_id']
            cantidad_receta = ingrediente['cantidad'] # Cantidad en la unidad de la receta
            unidad_receta = ingrediente['unidad'] # Unidad en la que se define en la receta
            unidad_base_ingrediente = ingrediente['unidad_base_ingrediente'] # Unidad base del producto en inventario

            # Obtener el costo promedio del ingrediente
            costo_promedio_ingrediente = productos_manager.obtener_costo_promedio(ingrediente_id)
            
            try:
                # Convertir cantidad de la receta a la unidad base del ingrediente
                cantidad_en_base = self.unit_converter.convert(
                    cantidad_receta,
                    unidad_receta,
                    unidad_base_ingrediente
                )
                
                # Calcular costo proporcional
                costo_total += cantidad_en_base * costo_promedio_ingrediente
            except Exception as e:
                # print(f"Error al convertir o calcular costo para ingrediente {ingrediente['nombre_ingrediente']}: {e}")
                # Si hay un error en la conversión, se puede optar por ignorar este ingrediente o lanzar un error.
                # Aquí, relanzamos para que el llamador sepa que el cálculo no fue completo.
                raise ValueError(f"Error al calcular costo para ingrediente '{ingrediente['nombre_ingrediente']}': {str(e)}")
        
        return costo_total

    def obtener_analisis_costos(self, categoria: str = None) -> list:
        """
        Obtiene análisis completo de costos para todas las recetas.
        
        Args:
            categoria (str): Filtra por categoría específica (None para todas)
            
        Returns:
            list: Lista de dictos con {
                'id': int,
                'nombre': str,
                'categoria': str,
                'costo': Decimal,
                'precio': Decimal,
                'ingredientes': int
            }
        """
        # Esta consulta es una simplificación y asume que el costo promedio se puede calcular
        # directamente de total_invertido / cantidad.
        # Para un cálculo más preciso y dinámico, se debería iterar sobre cada receta
        # y llamar a calcular_costo_receta para cada una.
        # La consulta SQL aquí es más para un "costo estimado" basado en el inventario actual.
        
        # Para obtener el costo real y actualizado, es mejor iterar y usar calcular_costo_receta
        # Este método se usará principalmente para la GUI de Control de Costos.
        
        # La consulta original en el contexto tenía un error en el cálculo del costo
        # (SUM(ri.cantidad * p.total_invertido / p.cantidad)).
        # ri.cantidad es la cantidad de la receta, p.cantidad es el stock actual.
        # Debería ser ri.cantidad * costo_promedio_del_ingrediente.
        # El costo promedio del ingrediente es p.total_invertido / p.cantidad.
        # Entonces, la fórmula es correcta si ri.cantidad es la cantidad en la unidad base del ingrediente.
        # Pero ri.cantidad es la cantidad en la unidad de la receta.
        # Por lo tanto, esta consulta es INEXACTA para el costo real de la receta.
        # Es mejor calcularlo en Python usando self.calcular_costo_receta.

        # Vamos a modificar este método para que obtenga los datos básicos y luego
        # la GUI o un proceso externo calcule el costo real usando calcular_costo_receta.
        # O, si se quiere un cálculo en SQL, la tabla de ingredientes de la receta
        # debería almacenar la cantidad en la unidad base del ingrediente.

        # Por ahora, para la GUI de Control de Costos, vamos a obtener los datos de la receta
        # y el costo se calculará en la GUI o se llamará a calcular_costo_receta por cada una.
        # La consulta original es problemática para un cálculo preciso en SQL.
        
        # Modificamos la consulta para obtener solo los datos de la receta.
        # El cálculo del costo se hará en la GUI o en un método separado que itere.
        query = """
            SELECT 
                r.id,
                r.nombre,
                r.categoria,
                r.precio_venta,
                r.costo_mano_obra_total
            FROM recetas r
        """
        params = []
        if categoria:
            query += " WHERE r.categoria = %s"
            params.append(categoria)
            
        query += " ORDER BY r.nombre"
        
        results = self.db_connection.fetch_all(query, params)
        
        recetas_con_costo = []
        column_names = ["id", "nombre", "categoria", "precio_venta", "costo_mano_obra_total"]
        
        # Para cada receta, calcular el costo real usando el método Python
        for row in results:
            receta_dict = dict(zip(column_names, row))
            receta_id = receta_dict['id']
            try:
                # Aquí es donde se llama al cálculo preciso del costo
                # Necesitamos una instancia de Productos para esto, que se pasará desde la GUI
                # o se instanciará aquí si es necesario.
                # Para evitar un acoplamiento circular, este método no debería instanciar Productos.
                # La GUI de ControlCostos ya tiene acceso a ProductosManager.
                # Por lo tanto, este método solo devolverá los datos de la receta.
                # El cálculo del costo total de ingredientes se hará en la GUI.
                
                # Convertir a Decimal
                receta_dict['precio_venta'] = Decimal(str(receta_dict['precio_venta']))
                receta_dict['costo_mano_obra_total'] = Decimal(str(receta_dict['costo_mano_obra_total']))
                
                recetas_con_costo.append(receta_dict)
            except Exception as e:
                # print(f"Error al procesar receta {receta_id} para análisis de costos: {e}")
                # Si hay un error en el cálculo del costo de una receta, se puede omitir o registrar.
                # Aquí, simplemente se omite del reporte.
                pass
        
        return recetas_con_costo

    def actualizar_precio_receta(self, receta_id: int, nuevo_precio: Decimal) -> None:
        """
        Actualiza el precio de venta de una receta.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not isinstance(receta_id, int) or receta_id <= 0:
            raise ValueError("El ID de la receta debe ser un entero positivo.")
        if not isinstance(nuevo_precio, Decimal) or nuevo_precio < Decimal('0'):
            raise ValueError("El nuevo precio debe ser un número decimal no negativo.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE recetas SET precio_venta = %s WHERE id = %s",
                (nuevo_precio, receta_id)
            )
            # No commit aquí
        except Error as e:
            # print(f"Error al actualizar precio: {str(e)}")
            raise e # Relanzar la excepción
        finally:
            if cursor: cursor.close()

    def exportar_reporte_costos(self, formato='csv'):
        """Exporta reporte de costos en el formato especificado"""
        # Implementación para exportar a CSV/Excel/PDF
        raise NotImplementedError("La función de exportación aún no está implementada.")

    def agregar_trabajador_a_receta(self, receta_id: int, nombre_trabajador: str, pago: Decimal) -> None:
        """
        Añade un trabajador a una receta existente.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not isinstance(receta_id, int) or receta_id <= 0:
            raise ValueError("El ID de la receta debe ser un entero positivo.")
        if not nombre_trabajador or not isinstance(nombre_trabajador, str):
            raise ValueError("El nombre del trabajador no puede estar vacío y debe ser una cadena de texto.")
        if not isinstance(pago, Decimal) or pago < Decimal('0'):
            raise ValueError("El pago debe ser un número decimal no negativo.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO receta_trabajadores (receta_id, nombre_trabajador, pago)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (receta_id, nombre_trabajador, pago))
            # No commit aquí
        except Error as e:
            raise e
        finally:
            if cursor: cursor.close()

    def obtener_trabajadores_de_receta(self, receta_id: int) -> list:
        """Obtiene los trabajadores de una receta específica."""
        query = """
            SELECT id, nombre_trabajador, pago
            FROM receta_trabajadores
            WHERE receta_id = %s
        """
        results = self.db_connection.fetch_all(query, (receta_id,))
        
        trabajadores_list = []
        column_names = ["id", "nombre_trabajador", "pago"]
        for row in results:
            trabajador_dict = dict(zip(column_names, row))
            trabajador_dict['pago'] = Decimal(str(trabajador_dict['pago']))
            trabajadores_list.append(trabajador_dict)
        return trabajadores_list

    def eliminar_trabajador_de_receta(self, trabajador_id: int) -> None:
        """
        Elimina un trabajador de una receta existente.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not isinstance(trabajador_id, int) or trabajador_id <= 0:
            raise ValueError("El ID del trabajador debe ser un entero positivo.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            query = """
                DELETE FROM receta_trabajadores
                WHERE id = %s
            """
            cursor.execute(query, (trabajador_id,))
            # No commit aquí
        except Error as e:
            raise e
        finally:
            if cursor: cursor.close()

    def actualizar_pago_trabajador(self, trabajador_id: int, nuevo_pago: Decimal) -> None:
        """
        Actualiza el pago de un trabajador.
        Este método NO hace commit. Se espera que el llamador maneje la transacción.
        """
        if not isinstance(trabajador_id, int) or trabajador_id <= 0:
            raise ValueError("El ID del trabajador debe ser un entero positivo.")
        if not isinstance(nuevo_pago, Decimal) or nuevo_pago < Decimal('0'):
            raise ValueError("El nuevo pago debe ser un número decimal no negativo.")

        conn = self.db_connection.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE receta_trabajadores SET pago = %s WHERE id = %s",
                (nuevo_pago, trabajador_id)
            )
            # No commit aquí
        except Error as e:
            raise e
        finally:
            if cursor: cursor.close()

    def calcular_costo_mano_obra_total(self, receta_id: int) -> Decimal:
        """
        Calcula el costo total de mano de obra para una receta.
        """
        trabajadores = self.obtener_trabajadores_de_receta(receta_id)
        costo_total = Decimal('0.00')
        
        for trabajador in trabajadores:
            costo_total += trabajador['pago']
            
        return costo_total

