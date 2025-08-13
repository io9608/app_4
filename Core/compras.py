import mysql.connector
from mysql.connector import Error
from decimal import Decimal
from Core.database import Database
from Core.productos import Productos
from Core.UnitConverter import UnitConverter

class Compras:
    def __init__(self, db: Database, productos_manager: Productos):
        self.db = db
        self.productos_manager = productos_manager
        self.unit_converter = UnitConverter()

    def registrar_compra(self, nombre_producto: str, cantidad: Decimal, unidad: str,
                        precio_unitario: Decimal, tipo_compra: str, 
                        proveedor: str = None, notas: str = None,
                        peso_por_paquete: Decimal = None,
                        unidades_por_paquete: int = None,
                        stock_minimo: Decimal = None, # Nuevo: para productos nuevos
                        unidad_display: str = None # Nuevo: para productos nuevos
                        ) -> bool:
        """
        Registra una compra y actualiza el inventario.
        Si el producto no existe, lo crea.
        
        Returns:
            bool: True si la compra se registró exitosamente
        """
        # Validaciones iniciales de entrada
        if not nombre_producto or not isinstance(nombre_producto, str):
            raise ValueError("El nombre del producto es obligatorio y debe ser una cadena de texto.")
        if not isinstance(cantidad, Decimal) or cantidad <= Decimal('0'):
            raise ValueError("La cantidad debe ser un número decimal positivo.")
        if not unidad or not isinstance(unidad, str):
            raise ValueError("La unidad de compra es obligatoria y debe ser una cadena de texto.")
        if not isinstance(precio_unitario, Decimal) or precio_unitario <= Decimal('0'):
            raise ValueError("El precio unitario debe ser un número decimal positivo.")
        if tipo_compra not in ['granel', 'paquete', 'unidad']:
            raise ValueError("Tipo de compra inválido. Debe ser 'granel', 'paquete' o 'unidad'.")
        
        # Validaciones específicas para tipo_compra 'paquete'
        if tipo_compra == 'paquete':
            if peso_por_paquete is None and unidades_por_paquete is None:
                raise ValueError("Para compra por paquete, 'peso_por_paquete' o 'unidades_por_paquete' es obligatorio.")
            if peso_por_paquete is not None and (not isinstance(peso_por_paquete, Decimal) or peso_por_paquete <= Decimal('0')):
                raise ValueError("El peso por paquete debe ser un número decimal positivo.")
            if unidades_por_paquete is not None and (not isinstance(unidades_por_paquete, int) or unidades_por_paquete <= 0):
                raise ValueError("Las unidades por paquete deben ser un número entero positivo.")

        # Iniciar la transacción
        self.db.get_connection() # Asegurarse de que la conexión esté activa antes de la transacción
        try:
            self.db.commit() # Asegurarse de que no haya transacciones pendientes antes de iniciar una nueva
            # (Esto es una precaución, si el sistema está bien diseñado, no debería haber transacciones pendientes aquí)
        except Error:
            self.db.rollback() # Si hay una transacción pendiente, revertirla

        try:
            self.db.get_connection().start_transaction() # Iniciar la transacción explícitamente

            # 1. Obtener o crear el producto
            producto_data = self.productos_manager.obtener_producto_por_nombre(nombre_producto)
            
            # Determinar la unidad base y unidad display del producto
            if producto_data:
                producto_id = producto_data[0] # ID del producto existente
                unidad_base_producto = producto_data[3] # 'unidad' en la tabla productos
                unidad_display_producto = producto_data[7] # 'unidad_display' en la tabla productos
                # Para productos existentes, stock_minimo y unidad_display se ignoran si se pasan,
                # ya que se usan los valores existentes del producto.
                # Si se desea permitir la actualización de estos campos en una compra,
                # la lógica de agregar_o_actualizar_producto debería manejarlo.
                # Por ahora, se pasan los valores existentes para no modificarlos accidentalmente.
                stock_minimo_a_usar = producto_data[6]
                unidad_display_a_usar = producto_data[7]
            else:
                # Si el producto es nuevo, stock_minimo y unidad_display son obligatorios
                if stock_minimo is None or unidad_display is None:
                    raise ValueError("Para un producto nuevo, 'stock_minimo' y 'unidad_display' son obligatorios.")
                if not isinstance(stock_minimo, Decimal) or stock_minimo < Decimal('0'):
                    raise ValueError("Para un producto nuevo, el stock mínimo debe ser un número decimal no negativo.")
                if not unidad_display or not isinstance(unidad_display, str):
                    raise ValueError("Para un producto nuevo, la unidad de visualización es obligatoria y debe ser una cadena de texto.")

                # Para un producto nuevo, la unidad base será la unidad_display inicial
                unidad_base_producto = unidad_display # La unidad base del producto será la unidad_display
                unidad_display_producto = unidad_display
                
                producto_id = None # Se obtendrá después de la llamada a agregar_o_actualizar_producto
                stock_minimo_a_usar = stock_minimo
                unidad_display_a_usar = unidad_display

            # 2. Calcular cantidad_base y el costo unitario en la unidad base del producto
            cantidad_a_sumar_a_stock = Decimal('0.00')
            costo_unitario_en_unidad_base = Decimal('0.00')

            if tipo_compra == 'granel' or tipo_compra == 'unidad':
                # Convertir la cantidad comprada a la unidad base del producto
                cantidad_a_sumar_a_stock = self.unit_converter.convert(cantidad, unidad, unidad_base_producto)
                
                # Calcular el costo total de esta compra (en la moneda original)
                costo_total_de_esta_compra = cantidad * precio_unitario 
                
                # Calcular el costo unitario en la unidad base del producto
                if cantidad_a_sumar_a_stock > 0:
                    costo_unitario_en_unidad_base = costo_total_de_esta_compra / cantidad_a_sumar_a_stock
                else:
                    costo_unitario_en_unidad_base = Decimal('0.00') # Evitar división por cero
                
            elif tipo_compra == 'paquete':
                cantidad_total_en_paquete_unidad_compra = Decimal('0.00')
                if peso_por_paquete is not None:
                    cantidad_total_en_paquete_unidad_compra = cantidad * peso_por_paquete
                elif unidades_por_paquete is not None:
                    cantidad_total_en_paquete_unidad_compra = cantidad * Decimal(str(unidades_por_paquete))

                if cantidad_total_en_paquete_unidad_compra <= 0:
                    raise ValueError("La cantidad total en el paquete debe ser positiva.")

                # Convertir la cantidad total comprada a la unidad base del producto
                cantidad_a_sumar_a_stock = self.unit_converter.convert(
                    cantidad_total_en_paquete_unidad_compra, unidad, unidad_base_producto
                )
                
                # Calcular el costo total de la compra
                costo_total_de_esta_compra = cantidad * precio_unitario # Cantidad de paquetes * precio por paquete
                
                # Calcular el precio unitario del producto en su unidad base
                if cantidad_a_sumar_a_stock > 0:
                    costo_unitario_en_unidad_base = costo_total_de_esta_compra / cantidad_a_sumar_a_stock
                else:
                    costo_unitario_en_unidad_base = Decimal('0.00') # Evitar división por cero

            # 3. Usar agregar_o_actualizar_producto para manejar el producto y su stock/costo
            # Este método devuelve el ID del producto (existente o recién creado)
            producto_id = self.productos_manager.agregar_o_actualizar_producto(
                nombre_producto=nombre_producto,
                cantidad_compra=cantidad_a_sumar_a_stock,
                unidad_interna_base=unidad_base_producto, # Siempre la unidad base del producto
                precio_unitario_compra_por_unidad_interna_base=costo_unitario_en_unidad_base,
                stock_minimo=stock_minimo_a_usar, 
                unidad_display=unidad_display_a_usar,
                proveedor=proveedor
            )

            # 4. Insertar registro de compra en la tabla 'compras'
            query = """
            INSERT INTO compras (
                producto_id, cantidad, unidad, precio_unitario, tipo_compra,
                proveedor, notas, peso_por_paquete, unidades_por_paquete
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # Pasar Decimal directamente a los parámetros de la consulta
            params = (
                producto_id, cantidad, unidad, precio_unitario, tipo_compra,
                proveedor, notas, 
                peso_por_paquete, # Pasa Decimal o None
                unidades_por_paquete
            )
            
            self.db.execute_query(query, params)
            
            self.db.commit() # Confirmar la transacción completa
            return True
            
        except Error as e:
            self.db.rollback() # Revertir si hay algún error de DB
            raise Exception(f"Error de base de datos al registrar compra: {str(e)}") # Relanzar como excepción general
        except ValueError as e:
            self.db.rollback() # Revertir si hay algún error de validación
            raise ValueError(f"Error de validación al registrar compra: {str(e)}") # Relanzar como ValueError
        except Exception as e:
            self.db.rollback() # Revertir para cualquier otro error inesperado
            raise Exception(f"Error inesperado al registrar compra: {str(e)}")

    def obtener_historial(self, days: int = 7, producto_id: int = None) -> list:
        """Obtiene el historial de compras."""
        if not isinstance(days, int) or days <= 0:
            raise ValueError("El número de días debe ser un entero positivo.")

        query = """
        SELECT c.fecha_compra, p.nombre_producto, c.cantidad, c.unidad, c.precio_unitario, 
               (c.cantidad * c.precio_unitario) as precio_total_calculado, 
               c.tipo_compra, c.proveedor, c.notas, c.peso_por_paquete, c.unidades_por_paquete
        FROM compras c
        JOIN productos p ON c.producto_id = p.id
        WHERE c.fecha_compra >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        params = [days]
        
        if producto_id:
            query += " AND c.producto_id = %s"
            params.append(producto_id)
            
        query += " ORDER BY c.fecha_compra DESC"
        
        try:
            results = self.db.fetch_all(query, params)
            
            compras_dict = []
            # Obtener nombres de columnas para mapear resultados a diccionarios
            # Esto requiere un cursor de diccionario o mapeo manual si fetch_all devuelve tuplas
            # Asumiendo que fetch_all devuelve tuplas y mapeamos manualmente
            column_names = ["fecha_compra", "nombre_producto", "cantidad", "unidad", "precio_unitario", 
                            "precio_total", "tipo_compra", "proveedor", "notas", "peso_por_paquete", "unidades_por_paquete"]
            
            for row in results:
                row_dict = dict(zip(column_names, row))
                # Asegurarse de que los valores Decimal se mantengan como Decimal
                row_dict['cantidad'] = Decimal(str(row_dict['cantidad']))
                row_dict['precio_unitario'] = Decimal(str(row_dict['precio_unitario']))
                row_dict['precio_total'] = Decimal(str(row_dict['precio_total'])) # Ya calculado en la query
                if row_dict['peso_por_paquete'] is not None:
                    row_dict['peso_por_paquete'] = Decimal(str(row_dict['peso_por_paquete']))
                compras_dict.append(row_dict)
            
            return compras_dict
        except Error as e:
            # print(f"Error al obtener historial de compras: {e}")
            raise e # Relanzar la excepción para que la GUI la maneje
        except Exception as e:
            raise Exception(f"Error inesperado al obtener historial de compras: {str(e)}")

