import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal
from datetime import datetime
from mysql.connector import Error
from Core.productos import Productos
from Core.UnitConverter import UnitConverter

class Produccion:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.productos_manager = Productos(db_connection)
        self.unit_converter = UnitConverter()

    def registrar_produccion(self, nombre_producto_elaborado: str, ingredientes: list, cantidad_producida: Decimal, unidad_producida: str) -> int:
        """
        Registra la producción de un producto elaborado ad-hoc con soporte para unidades específicas.
        
        Args:
            nombre_producto_elaborado: Nombre del producto creado
            ingredientes: Lista de tuplas (ingrediente_id, cantidad_TOTAL_usada, unidad_ingrediente)
            cantidad_producida: Número de unidades del producto elaborado
            unidad_producida: Unidad de medida para el producto elaborado
        
        Returns:
            int: ID del producto elaborado
        """
        # Validaciones iniciales de entrada
        if not nombre_producto_elaborado or not isinstance(nombre_producto_elaborado, str):
            raise ValueError("El nombre del producto elaborado es obligatorio.")
        if not isinstance(cantidad_producida, Decimal) or cantidad_producida <= Decimal('0'):
            raise ValueError("La cantidad a producir debe ser un número decimal positivo.")
        if not isinstance(ingredientes, list) or not ingredientes:
            raise ValueError("La lista de ingredientes no puede estar vacía.")
        if not unidad_producida or not isinstance(unidad_producida, str):
            raise ValueError("La unidad de medida es obligatoria.")

        try:
            # 1. Calcular el costo total de los ingredientes
            costo_total_ingredientes_produccion = Decimal('0.00')
            ingredientes_a_consumir_en_base = []

            for ingrediente_id_raw, cantidad_total_usada_raw, unidad_ingrediente in ingredientes:
                ingrediente_id = int(ingrediente_id_raw)
                cantidad_total_usada = Decimal(str(cantidad_total_usada_raw))

                if cantidad_total_usada <= Decimal('0'):
                    raise ValueError(f"La cantidad usada para el ingrediente ID {ingrediente_id} debe ser positiva.")

                # Obtener el costo promedio de la materia prima
                costo_promedio_ingrediente = self.productos_manager.obtener_costo_promedio(ingrediente_id)

                # Obtener la unidad base del ingrediente
                ingrediente_data = self.productos_manager.obtener_producto(ingrediente_id)
                if not ingrediente_data:
                    raise ValueError(f"Materia prima con ID {ingrediente_id} no encontrada.")
                unidad_interna_base_ingrediente = ingrediente_data[3]

                # Convertir la cantidad a la unidad base
                cantidad_en_base = self.unit_converter.convert(
                    cantidad_total_usada, unidad_ingrediente, unidad_interna_base_ingrediente
                )

                # Acumular el costo total
                costo_total_ingredientes_produccion += costo_promedio_ingrediente * cantidad_en_base
                ingredientes_a_consumir_en_base.append((ingrediente_id, cantidad_en_base))

            # Calcular el costo por unidad
            costo_por_unidad = Decimal('0')
            if cantidad_producida > Decimal('0'):
                costo_por_unidad = costo_total_ingredientes_produccion / cantidad_producida

            # 3. Registrar el producto
            producto_id = self.productos_manager.agregar_o_actualizar_producto(
                nombre_producto=nombre_producto_elaborado,
                cantidad_compra=cantidad_producida,
                unidad_interna_base=unidad_producida,
                precio_unitario_compra_por_unidad_interna_base=costo_por_unidad,
                stock_minimo=Decimal('0'),
                unidad_display=unidad_producida,
                proveedor="Producción Interna"
            )

            # 4. Consumir ingredientes
            for ing_id, cantidad in ingredientes_a_consumir_en_base:
                self.productos_manager.decrementar_stock(ing_id, cantidad)

            # 5. Registrar en produccion_registro
            query = """
                INSERT INTO produccion_registro (producto_id, cantidad_producida, fecha_produccion, costo_por_unidad_elaborado)
                VALUES (%s, %s, %s, %s)
            """
            params = (producto_id, cantidad_producida, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), costo_por_unidad)
            self.db_connection.execute_query(query, params)

            return producto_id

        except Error as e:
            raise Exception(f"Error de base de datos al registrar producción: {str(e)}")
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise Exception(str(e))
