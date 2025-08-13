import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from decimal import Decimal
from Core.reportes import Reportes
from Core.recetas import RecetasManager
from Core.ventas import Ventas

class ResumenVentasPage(tk.Frame):
    def __init__(self, parent, reportes_manager, recetas_manager, ventas_manager):
        super().__init__(parent)
        self.reportes_manager = reportes_manager
        self.recetas_manager = recetas_manager
        self.ventas_manager = ventas_manager
        self.create_widgets()
        self.load_daily_data()

    def create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        main_frame = tk.Frame(self, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # Título
        tk.Label(
            main_frame, 
            text="Resumen de Ventas del Día", 
            font=("Helvetica", 16, "bold"),
            fg="#1E88E5"  # Azul principal
        ).grid(row=0, column=0, columnspan=4, pady=(0, 20), sticky="w")

        # Frame para resumen general
        summary_frame = ttk.LabelFrame(main_frame, text="Resumen General", padding=10)
        summary_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 20))
        summary_frame.columnconfigure(1, weight=1)

        # Etiquetas de resumen
        self.total_ventas_label = tk.Label(summary_frame, text="Total Ventas: $0.00", font=("Helvetica", 12, "bold"))
        self.total_ventas_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.total_clientes_label = tk.Label(summary_frame, text="Total Clientes: 0", font=("Helvetica", 12, "bold"))
        self.total_clientes_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        self.total_productos_label = tk.Label(summary_frame, text="Total Productos Vendidos: 0", font=("Helvetica", 12, "bold"))
        self.total_productos_label.grid(row=0, column=2, padx=10, pady=5, sticky="w")

        # Frame para productos vendidos
        products_frame = ttk.LabelFrame(main_frame, text="Productos Vendidos Hoy", padding=10)
        products_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 20))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Treeview para productos vendidos
        self.tree_productos = ttk.Treeview(products_frame, columns=(
            "nombre", "cantidad", "precio_unitario", "total"
        ), show='headings', style="Modern.Treeview")

        self.tree_productos.heading("nombre", text="Producto")
        self.tree_productos.heading("cantidad", text="Cantidad")
        self.tree_productos.heading("precio_unitario", text="Precio Unitario")
        self.tree_productos.heading("total", text="Total")

        self.tree_productos.column("nombre", width=200)
        self.tree_productos.column("cantidad", width=100, anchor="center")
        self.tree_productos.column("precio_unitario", width=120, anchor="e")
        self.tree_productos.column("total", width=120, anchor="e")

        self.tree_productos.pack(fill="both", expand=True, side="left")

        # Scrollbar para productos
        products_scrollbar = ttk.Scrollbar(products_frame, orient="vertical", command=self.tree_productos.yview)
        products_scrollbar.pack(side="right", fill="y")
        self.tree_productos.configure(yscrollcommand=products_scrollbar.set)

        # Frame para pagos a trabajadores
        workers_frame = ttk.LabelFrame(main_frame, text="Pagos a Trabajadores", padding=10)
        workers_frame.grid(row=2, column=2, columnspan=2, sticky="nsew", pady=(0, 20))
        main_frame.columnconfigure(2, weight=1)

        # Treeview para pagos a trabajadores
        self.tree_pagos = ttk.Treeview(workers_frame, columns=(
            "receta", "pago"
        ), show='headings', style="Modern.Treeview")

        self.tree_pagos.heading("receta", text="Receta")
        self.tree_pagos.heading("pago", text="Pago ($)")

        self.tree_pagos.column("receta", width=200)
        self.tree_pagos.column("pago", width=120, anchor="e")

        self.tree_pagos.pack(fill="both", expand=True, side="left")

        # Scrollbar para pagos
        workers_scrollbar = ttk.Scrollbar(workers_frame, orient="vertical", command=self.tree_pagos.yview)
        workers_scrollbar.pack(side="right", fill="y")
        self.tree_pagos.configure(yscrollcommand=workers_scrollbar.set)

        # Frame para ingresos y ganancias
        earnings_frame = ttk.LabelFrame(main_frame, text="Resumen Financiero", padding=10)
        earnings_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(0, 20))

        self.total_ingresos_label = tk.Label(earnings_frame, text="Ingresos Totales: $0.00", font=("Helvetica", 12, "bold"))
        self.total_ingresos_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.total_pagos_label = tk.Label(earnings_frame, text="Pagos a Trabajadores: $0.00", font=("Helvetica", 12, "bold"))
        self.total_pagos_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        self.ganancia_neta_label = tk.Label(earnings_frame, text="Ganancia Neta: $0.00", font=("Helvetica", 14, "bold"), fg="#4CAF50")
        self.ganancia_neta_label.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # Botón para actualizar datos
        ttk.Button(main_frame, text="Actualizar Datos", command=self.load_daily_data, style="Accent.TButton").grid(
            row=4, column=0, columnspan=4, pady=(20, 0)
        )

    def load_daily_data(self):
        """Carga los datos del día"""
        try:
            # Obtener ventas del día
            ventas_hoy = self.obtener_ventas_del_dia()
            
            # Limpiar treeviews
            for item in self.tree_productos.get_children():
                self.tree_productos.delete(item)
                
            for item in self.tree_pagos.get_children():
                self.tree_pagos.delete(item)
            
            # Variables para cálculos
            total_ventas = Decimal('0.00')
            total_clientes = set()
            total_productos = 0
            total_ingresos = Decimal('0.00')
            total_pagos = Decimal('0.00')
            
            # Diccionario para agrupar productos
            productos_agrupados = {}
            
            # Procesar ventas
            for venta in ventas_hoy:
                # Extraer datos de la venta
                venta_id = venta[0]
                nombre_receta = venta[1]
                cantidad_vendida = venta[2]
                precio_venta = Decimal(str(venta[3]))
                cliente_nombre = venta[4]
                fecha_venta = venta[5]
                
                # Acumular datos
                total_ventas += 1
                total_productos += cantidad_vendida
                if cliente_nombre:
                    total_clientes.add(cliente_nombre)
                
                # Calcular totales
                subtotal = precio_venta * Decimal(str(cantidad_vendida))
                total_ingresos += subtotal
                
                # Agrupar productos
                if nombre_receta in productos_agrupados:
                    productos_agrupados[nombre_receta]['cantidad'] += cantidad_vendida
                    productos_agrupados[nombre_receta]['total'] += subtotal
                else:
                    productos_agrupados[nombre_receta] = {
                        'cantidad': cantidad_vendida,
                        'precio_unitario': precio_venta,
                        'total': subtotal
                    }
            
            # Insertar productos en el treeview
            for nombre, datos in productos_agrupados.items():
                self.tree_productos.insert("", "end", values=(
                    nombre,
                    datos['cantidad'],
                    f"${datos['precio_unitario']:.2f}",
                    f"${datos['total']:.2f}"
                ))
            
            # Obtener pagos a trabajadores
            recetas = self.recetas_manager.obtener_todas_las_recetas()
            for receta in recetas:
                pago_trabajadores = Decimal(str(receta.get('costo_mano_obra_total', 0)))
                if pago_trabajadores > 0:
                    self.tree_pagos.insert("", "end", values=(
                        receta['nombre'],
                        f"${pago_trabajadores:.2f}"
                    ))
                    total_pagos += pago_trabajadores
            
            # Actualizar etiquetas de resumen
            self.total_ventas_label.config(text=f"Total Ventas: {total_ventas}")
            self.total_clientes_label.config(text=f"Total Clientes: {len(total_clientes)}")
            self.total_productos_label.config(text=f"Total Productos Vendidos: {total_productos}")
            self.total_ingresos_label.config(text=f"Ingresos Totales: ${total_ingresos:.2f}")
            self.total_pagos_label.config(text=f"Pagos a Trabajadores: ${total_pagos:.2f}")
            
            # Calcular y mostrar ganancia neta
            ganancia_neta = total_ingresos - total_pagos
            self.ganancia_neta_label.config(text=f"Ganancia Neta: ${ganancia_neta:.2f}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos del día: {str(e)}")

    def obtener_ventas_del_dia(self):
        """Obtiene las ventas del día actual"""
        try:
            # Obtener la fecha de hoy en formato YYYY-MM-DD
            hoy = date.today().strftime('%Y-%m-%d')
            
            # Consulta para obtener ventas del día
            query = """
                SELECT v.id, r.nombre, v.cantidad_vendida, v.precio_venta, 
                       v.cliente_nombre, v.fecha_venta
                FROM ventas v
                JOIN recetas r ON v.producto_id = r.id
                WHERE DATE(v.fecha_venta) = %s
                ORDER BY v.fecha_venta DESC
            """
            
            return self.reportes_manager.db_connection.fetch_all(query, (hoy,))
        except Exception as e:
            raise Exception(f"Error al obtener ventas del día: {str(e)}")
