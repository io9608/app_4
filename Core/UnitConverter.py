# /app_3/Core/unit_converter.py
"""
Módulo para convertir unidades de medida (masa, volumen, etc.)
Soporta kg, g, mg, L, mL, unidades, etc.
"""

from decimal import Decimal, getcontext

class UnitConverter:
    # Factores de conversión (base: gramos para masa, litros para volumen, metros para longitud, etc.)
    # Se agrupan por tipo de magnitud para facilitar la validación y evitar conversiones entre tipos.
    CONVERSION_FACTORS = {
        # Masa (Base: gramos)
        'g': Decimal('1'),
        'kg': Decimal('1000'),
        'mg': Decimal('0.001'),
        'lb': Decimal('453.59237'), # Libra (avoirdupois)
        'oz': Decimal('28.349523125'), # Onza (avoirdupois)
        'ton': Decimal('907184.74'), # Tonelada corta (US)
        't': Decimal('1000000'), # Tonelada métrica (megagramo)
        
        # Volumen (Base: litros)
        'L': Decimal('1'),
        'mL': Decimal('0.001'),
        'dL': Decimal('0.1'), # Decilitro
        'cL': Decimal('0.01'), # Centilitro
        'kL': Decimal('1000'), # Kilolitro
        'gal': Decimal('3.785411784'), # Galón (US liquid)
        'qt': Decimal('0.946352946'), # Cuarto de galón (US liquid)
        'pt': Decimal('0.473176473'), # Pinta (US liquid)
        'cup': Decimal('0.236588236'), # Taza (US liquid)
        'fl_oz': Decimal('0.0295735295625'), # Onza líquida (US)
        'tbsp': Decimal('0.01478676478125'), # Cucharada (US)
        'tsp': Decimal('0.00492892159375'), # Cucharadita (US)
        'm3': Decimal('1000'), # Metro cúbico
        'cm3': Decimal('0.001'), # Centímetro cúbico (equivale a mL)
        
        # Longitud (Base: metros)
        'm': Decimal('1'),
        'km': Decimal('1000'),
        'cm': Decimal('0.01'),
        'mm': Decimal('0.001'),
        'in': Decimal('0.0254'), # Pulgada
        'ft': Decimal('0.3048'), # Pie
        'yd': Decimal('0.9144'), # Yarda
        'mi': Decimal('1609.344'), # Milla
        
        # Área (Base: metros cuadrados)
        'm2': Decimal('1'),
        'km2': Decimal('1000000'),
        'cm2': Decimal('0.0001'),
        'mm2': Decimal('0.000001'),
        'ha': Decimal('10000'), # Hectárea
        'acre': Decimal('4046.8564224'), # Acre
        'ft2': Decimal('0.09290304'), # Pie cuadrado
        'in2': Decimal('0.00064516'), # Pulgada cuadrada
        
        # Tiempo (Base: segundos)
        's': Decimal('1'),
        'ms': Decimal('0.001'),
        'min': Decimal('60'),
        'hr': Decimal('3600'),
        'day': Decimal('86400'),
        
        # Conteo / Unidades (Base: unidad)
        'unidad': Decimal('1'),
        'docena': Decimal('12'),
        'caja': Decimal('1'), # Asumimos que 'caja' es una unidad de conteo, su valor real dependerá del contexto
        'paquete': Decimal('1'), # Similar a 'caja', su valor dependerá del contexto
        'rollo': Decimal('1'),
        'resma': Decimal('500'), # Resma de papel
    }

    # Mapeo de unidades a sus tipos de magnitud para validación
    UNIT_TYPES = {
        'g': 'masa', 'kg': 'masa', 'mg': 'masa', 'lb': 'masa', 'oz': 'masa', 'ton': 'masa', 't': 'masa',
        'L': 'volumen', 'mL': 'volumen', 'dL': 'volumen', 'cL': 'volumen', 'kL': 'volumen', 'gal': 'volumen',
        'qt': 'volumen', 'pt': 'volumen', 'cup': 'volumen', 'fl_oz': 'volumen', 'tbsp': 'volumen', 'tsp': 'volumen',
        'm3': 'volumen', 'cm3': 'volumen',
        'm': 'longitud', 'km': 'longitud', 'cm': 'longitud', 'mm': 'longitud', 'in': 'longitud', 'ft': 'longitud',
        'yd': 'longitud', 'mi': 'longitud',
        'm2': 'area', 'km2': 'area', 'cm2': 'area', 'mm2': 'area', 'ha': 'area', 'acre': 'area', 'ft2': 'area', 'in2': 'area',
        's': 'tiempo', 'ms': 'tiempo', 'min': 'tiempo', 'hr': 'tiempo', 'day': 'tiempo',
        'unidad': 'conteo', 'docena': 'conteo', 'caja': 'conteo', 'paquete': 'conteo', 'rollo': 'conteo', 'resma': 'conteo',
    }

    def __init__(self):
        # Aumentar la precisión para cálculos financieros y científicos
        getcontext().prec = 10 # Precisión decimal para cálculos (ej. 10 dígitos significativos)

    def convert(self, valor, unidad_origen, unidad_destino):
        """
        Convierte un valor de una unidad a otra (ej: 1 kg → 1000 g).
        
        Args:
            valor (Decimal/float): Valor a convertir.
            unidad_origen (str): Unidad de origen (ej: 'kg', 'g', 'L').
            unidad_destino (str): Unidad de destino (ej: 'g', 'mL').
        
        Returns:
            Decimal: Valor convertido con precisión alta.
        """
        valor = Decimal(str(valor))  # Asegurar que sea Decimal
        
        # Validar que las unidades existan
        if unidad_origen not in self.CONVERSION_FACTORS:
            raise ValueError(f"Unidad de origen '{unidad_origen}' no soportada. Disponibles: {list(self.CONVERSION_FACTORS.keys())}")
        if unidad_destino not in self.CONVERSION_FACTORS:
            raise ValueError(f"Unidad de destino '{unidad_destino}' no soportada. Disponibles: {list(self.CONVERSION_FACTORS.keys())}")
        
        # Validar que las unidades sean del mismo tipo de magnitud
        tipo_origen = self.UNIT_TYPES.get(unidad_origen)
        tipo_destino = self.UNIT_TYPES.get(unidad_destino)

        if tipo_origen is None or tipo_destino is None:
            # Esto no debería pasar si las unidades ya pasaron la primera validación,
            # pero es una buena medida de seguridad.
            raise ValueError(f"Tipo de magnitud no definido para '{unidad_origen}' o '{unidad_destino}'.")

        if tipo_origen != tipo_destino:
            raise ValueError(f"No se puede convertir de '{unidad_origen}' ({tipo_origen}) a '{unidad_destino}' ({tipo_destino}). Las unidades deben ser del mismo tipo de magnitud.")
        
        # Convertir a la unidad base del tipo de magnitud
        valor_en_base = valor * self.CONVERSION_FACTORS[unidad_origen]
        
        # Convertir de la unidad base a la unidad de destino
        if self.CONVERSION_FACTORS[unidad_destino] == Decimal('0'):
            raise ValueError(f"Factor de conversión a cero para la unidad de destino '{unidad_destino}'.")
            
        valor_convertido = valor_en_base / self.CONVERSION_FACTORS[unidad_destino]
        
        return valor_convertido

    def get_valid_units(self):
        """Lista de unidades soportadas (para Combobox, por ejemplo)."""
        return list(self.CONVERSION_FACTORS.keys())

    def get_units_by_type(self, unit_type: str):
        """
        Devuelve una lista de unidades para un tipo de magnitud específico.
        Ej: get_units_by_type('masa') -> ['g', 'kg', 'mg', 'lb', 'oz', 'ton', 't']
        """
        return [unit for unit, u_type in self.UNIT_TYPES.items() if u_type == unit_type]

