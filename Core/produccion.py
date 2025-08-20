import mysql.connector
from mysql.connector import Error
from datetime import datetime
from decimal import Decimal
from Core.productos import Productos
from Core.UnitConverter import UnitConverter

class Produccion:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.productos_manager = Productos(db_connection)
        self.unit_converter = UnitConverter()

    def registrar_produccion(self, nombre_producto_elaborado: str, ingredientes: list, cantidad_producida: Decimal) -> int:
        """
        Registra la producción de un producto elaborado ad-hoc.
        - nombre_producto_elaborado: Nombre del producto creado (ej: "Pan").
        - ingredientes: Lista de tuplas (ingrediente_id, cantidad_TOTAL_usada, unidad_ingrediente).
                        'cantidad_TOTAL_usada' es la cantidad TOTAL de ingrediente para la producción completa.
        - cantidad_producida: Número de unidades del producto elaborado.
        
        Returns:
            int: ID del producto elaborado (existente o recién creado).
        """
        # Validaciones iniciales de entrada
        if not nombre_producto_elaborado or not isinstance(nombre_producto_elaborado, str):
            raise ValueError("El nombre del producto elaborado es obligatorio y debe ser una cadena de texto.")
        if not isinstance(cantidad_producida, Decimal) or cantidad_producida <= Decimal('0'):
            raise ValueError("La cantidad a producir debe ser un número decimal positivo.")
        if not isinstance(ingredientes, list) or not ingredientes:
            raise ValueError("La lista de ingredientes no puede estar vacía.")
        
        # Iniciar la transacción
        self.db_connection.get_connection() # Asegurarse de que la conexión esté activa
        try:
            self.db_connection.commit() # Limpiar cualquier transacción pendiente
        except Error:
            self.db_connection.rollback() # Si hay una transacción pendiente, revertirla

        try:
            self.db_connection.get_connection().start_transaction() # Iniciar la transacción explícitamente

            # 1. Calcular el costo total de los ingredientes para esta producción
            costo_total_ingredientes_produccion = Decimal('0.00')
            ingredientes_a_consumir_en_base = [] # Para almacenar (ingrediente_id, cantidad_en_base)

            for ingrediente_id_raw, cantidad_total_usada_raw, unidad_ingrediente in ingredientes:
                ingrediente_id = int(ingrediente_id_raw) # Asegurarse de que sea int
                cantidad_total_usada = Decimal(str(cantidad_total_usada_raw)) # Asegurarse de que sea Decimal

                if cantidad_total_usada <= Decimal('0'):
                    raise ValueError(f"La cantidad usada para el ingrediente ID {ingrediente_id} debe ser positiva.")
                if not unidad_ingrediente or not isinstance(unidad_ingrediente, str):
                    raise ValueError(f"La unidad para el ingrediente ID {ingrediente_id} es obligatoria.")

                # Obtener el costo promedio de la materia prima
                costo_promedio_ingrediente = self.productos_manager.obtener_costo_promedio(ingrediente_id)
                
                # Obtener la unidad interna base del ingrediente para la conversión
                ingrediente_data = self.productos_manager.obtener_producto(ingrediente_id)
                if not ingrediente_data:
                    raise ValueError(f"Materia prima con ID {ingrediente_id} no encontrada.")
                unidad_interna_base_ingrediente = ingrediente_data[3] # 'unidad' en la tabla productos

                # Convertir la cantidad TOTAL del ingrediente a su unidad interna base
                cantidad_total_en_base = self.unit_converter.convert(
                    cantidad_total_usada, unidad_ingrediente, unidad_interna_base_ingrediente
                )
                
                # Acumular el costo total de los ingredientes para la producción completa
                costo_total_ingredientes_produccion += costo_promedio_ingrediente * cantidad_total_en_base
                
                ingredientes_a_consumir_en_base.append((ingrediente_id, cantidad_total_en_base))

            # 2. Calcular el costo por unidad del producto elaborado
            costo_por_unidad_elaborado = Decimal('0.00')
            if cantidad_producida > Decimal('0'):
                costo_por_unidad_elaborado = costo_total_ingredientes_produccion / cantidad_producida
            else:
                # Esto ya se valida al inicio, pero es una doble verificación
                raise ValueError("La cantidad a producir debe ser mayor que cero para calcular el costo por unidad.")

            # 3. Verificar stock de todos los ingredientes primero (antes de cualquier decremento)
            for ingrediente_id, cantidad_total_en_base in ingredientes_a_consumir_en_base:
                # Obtener el stock actual del ingrediente
                ingrediente_data = self.productos_manager.obtener_producto(ingrediente_id)
                if not ingrediente_data:
                    raise ValueError(f"Materia prima con ID {ingrediente_id} no encontrada durante la verificación de stock.")
                
                stock_actual_ingrediente = Decimal(str(ingrediente_data[2])) # índice de cantidad
                nombre_ingrediente = ingrediente_data[1]
                unidad_base_ingrediente = ingrediente_data[3]

                if stock_actual_ingrediente < cantidad_total_en_base:
                    raise ValueError(f"Stock insuficiente para el ingrediente '{nombre_ingrediente}'. Disponible: {stock_actual_ingrediente:.4f} {unidad_base_ingrediente}, Requerido: {cantidad_total_en_base:.4f} {unidad_base_ingrediente}")

            # 4. Registrar el producto elaborado en la tabla productos (si no existe) o actualizar su stock y total_invertido
            # El total_invertido para el producto elaborado es el costo total de los ingredientes usados en esta producción
            producto_id = self.productos_manager.agregar_o_actualizar_producto(
                nombre_producto=nombre_producto_elaborado,
                cantidad_compra=cantidad_producida,  # Cantidad del producto elaborado
                unidad_interna_base="unidad",  # Asumimos "unidad" como base para productos elaborados
                precio_unitario_compra_por_unidad_interna_base=costo_por_unidad_elaborado,  # Costo por unidad del elaborado
                stock_minimo=Decimal('0.00'),  # Se puede ajustar si se desea un stock mínimo para pre-elaborados
                unidad_display="unidad",  # Unidad de visualización para el producto elaborado
                proveedor="Producción Interna" # Asignar un proveedor por defecto para productos elaborados
            )

            # 5. Consumir los ingredientes (decrementar stock)
            for ingrediente_id, cantidad_total_en_base in ingredientes_a_consumir_en_base:
                # Pasar Decimal directamente a decrementar_stock
                self.productos_manager.decrementar_stock(ingrediente_id, cantidad_total_en_base)

            # 6. Registrar en produccion_registro (para historial)
            # Asegurarse de que la tabla se llama 'produccion_registro' y no 'produccion_rregistro'
            query_registro = """
                INSERT INTO produccion_registro (producto_id, cantidad_producida, fecha_produccion, costo_por_unidad_elaborado)
                VALUES (%s, %s, %s, %s)
            """
            params_registro = (producto_id, cantidad_producida, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), costo_por_unidad_elaborado)
            self.db_connection.execute_query(query_registro, params_registro)

            self.db_connection.commit() # Confirmar la transacción completa
            return producto_id

        except Error as e:
            self.db_connection.rollback()
            raise Exception(f"Error de base de datos al registrar producción: {str(e)}")
        except ValueError as e:
            self.db_connection.rollback()
            raise ValueError(f"Error de validación al registrar producción: {str(e)}")
        except Exception as e:
            self.db_connection.rollback()
            raise Exception(f"Error inesperado al registrar producción: {str(e)}")

