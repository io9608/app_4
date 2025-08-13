import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

class CashFlowPage(tk.Frame):
    def __init__(self, parent, reportes_manager, ventas_manager, productos_manager, autoconsumo_manager):
        super().__init__(parent)
        self.reportes_manager = reportes_manager
        self.ventas_manager = ventas_manager
        self.productos_manager = productos_manager
        self.autoconsumo_manager = autoconsumo_manager
        
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        # Frame principal con padding
        main_frame = tk.Frame(self, background="#F5F5F5")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(
            main_frame, 
            text="Flujo de Caja y Análisis Financiero", 
            font=("Segoe UI", 16, "bold"),
            background="#F5F5F5",
            foreground="#1E88E5"
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20), sticky="w")
        
        # Frame para resumen financiero
        resumen_frame = ttk.LabelFrame(main_frame, text="Resumen Financiero", padding=15, style="Card.TFrame")
        resumen_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 20))
        resumen_frame.columnconfigure((0, 1, 2, 3), weight=1)
        
        # Etiquetas para resumen
        self.label_total_ventas = ttk.Label(resumen_frame, text="Total Ventas: $0.00", style="Highlight.TLabel")
        self.label_total_ventas.grid(row=0, column=0, padx=10, pady=5)
        
        self.label_total_costos = ttk.Label(resumen_frame, text="Total Costos: $0.00", style="Highlight.TLabel")
        self.label_total_costos.grid(row=0, column=1, padx=10, pady=5)
        
        self.label_total_ganancias = ttk.Label(resumen_frame, text="Total Ganancias: $0.00", style="Highlight.TLabel")
        self.label_total_ganancias.grid(row=0, column=2, padx=10, pady=5)
        
        self.label_total_autoconsumo = ttk.Label(resumen_frame, text="Total Autoconsumo: $0.00", style="Highlight.TLabel")
        self.label_total_autoconsumo.grid(row=0, column=3, padx=10, pady=5)
        
        # Frame para gráficos
        graficos_frame = ttk.LabelFrame(main_frame, text="Gráficos", padding=15, style="Card.TFrame")
        graficos_frame.grid(row=2, column=0, columnspan=4, sticky="nsew", pady=(0, 20))
        graficos_frame.columnconfigure((0, 1), weight=1)
        graficos_frame.rowconfigure((0, 1), weight=1)
        
        # Crear figura para gráfico de ventas semanales
        self.fig_ventas, self.ax_ventas = plt.subplots(figsize=(8, 4))
        self.fig_ventas.patch.set_facecolor('#F5F5F5')
        self.canvas_ventas = FigureCanvasTkAgg(self.fig_ventas, graficos_frame)
        self.canvas_ventas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Crear figura para gráfico de ganancias
        self.fig_ganancias, self.ax_ganancias = plt.subplots(figsize=(8, 4))
        self.fig_ganancias.patch.set_facecolor('#F5F5F5')
        self.canvas_ganancias = FigureCanvasTkAgg(self.fig_ganancias, graficos_frame)
        self.canvas_ganancias.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Crear figura para gráfico de productos más vendidos
        self.fig_productos, self.ax_productos = plt.subplots(figsize=(16, 4))
        self.fig_productos.patch.set_facecolor('#F5F5F5')
        self.canvas_productos = FigureCanvasTkAgg(self.fig_productos, graficos_frame)
        self.canvas_productos.get_tk_widget().grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(20, 0))
        
        # Botón para actualizar datos
        ttk.Button(main_frame, text="Actualizar Datos", command=self.load_data, style="Accent.TButton").grid(
            row=3, column=0, columnspan=4, pady=(10, 0)
        )
        
        # Configurar expansión
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

    def load_data(self):
        """Carga y muestra los datos financieros"""
        try:
            # Calcular totales
            total_ventas = Decimal(str(self.reportes_manager.obtener_total_ventas()))
            total_costos = Decimal(str(self.reportes_manager.obtener_total_costos()))
            total_autoconsumo = self.autoconsumo_manager.obtener_total_costo_autoconsumo()
            total_ganancias = total_ventas - total_costos - total_autoconsumo
            
            # Actualizar etiquetas de resumen
            self.label_total_ventas.config(text=f"Total Ventas: ${total_ventas:.2f}")
            self.label_total_costos.config(text=f"Total Costos: ${total_costos:.2f}")
            self.label_total_ganancias.config(text=f"Total Ganancias: ${total_ganancias:.2f}")
            self.label_total_autoconsumo.config(text=f"Total Autoconsumo: ${total_autoconsumo:.2f}")
            
            # Actualizar gráficos
            self.update_ventas_chart()
            self.update_ganancias_chart()
            self.update_productos_chart()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos financieros: {str(e)}")

    def update_ventas_chart(self):
        """Actualiza el gráfico de ventas semanales"""
        try:
            # Obtener ventas de los últimos 7 días
            ventas_diarias_data = self.reportes_manager.obtener_ventas_semanales()
            
            # Convertir fechas a objetos datetime
            ventas_diarias = []
            for fecha, total in ventas_diarias_data:
                if total is not None:
                    ventas_diarias.append((datetime.strptime(str(fecha), '%Y-%m-%d'), float(total)))
                else:
                    ventas_diarias.append((datetime.strptime(str(fecha), '%Y-%m-%d'), 0.0))
            
            # Preparar datos para el gráfico
            fechas = [v[0] for v in ventas_diarias]
            montos = [float(v[1]) for v in ventas_diarias]
            
            # Limpiar gráfico anterior
            self.ax_ventas.clear()
            
            # Crear gráfico de barras
            self.ax_ventas.bar(fechas, montos, color='#1E88E5')
            self.ax_ventas.set_title("Ventas Diarias (Últimos 7 Días)", fontsize=12, fontweight='bold')
            self.ax_ventas.set_ylabel("Monto ($)")
            self.ax_ventas.set_xlabel("Fecha")
            
            # Formatear eje X
            self.ax_ventas.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            self.ax_ventas.xaxis.set_major_locator(mdates.DayLocator())
            self.ax_ventas.tick_params(axis='x', rotation=45)
            
            # Ajustar diseño
            self.fig_ventas.tight_layout()
            
            # Actualizar canvas
            self.canvas_ventas.draw()
            
        except Exception as e:
            print(f"Error al actualizar gráfico de ventas: {e}")

    def obtener_ventas_diarias(self):
        """Obtiene las ventas diarias de los últimos 7 días"""
        try:
            conn = self.reportes_manager.db_connection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DATE(v.fecha_venta) as fecha, 
                       COALESCE(SUM(v.precio_venta * v.cantidad_vendida), 0) as total
                FROM ventas v
                WHERE v.fecha_venta >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(v.fecha_venta)
                ORDER BY fecha
            """)
            results = cursor.fetchall()
            cursor.close()
            
            # Convertir fechas a objetos datetime
            ventas = []
            for fecha, total in results:
                if total is not None:
                    ventas.append((datetime.strptime(str(fecha), '%Y-%m-%d'), float(total)))
                else:
                    ventas.append((datetime.strptime(str(fecha), '%Y-%m-%d'), 0.0))
                    
            # Completar días faltantes con 0
            if ventas:
                start_date = ventas[0][0]
                end_date = ventas[-1][0]
                all_dates = []
                current_date = start_date
                
                while current_date <= end_date:
                    found = False
                    for v in ventas:
                        if v[0].date() == current_date.date():
                            all_dates.append(v)
                            found = True
                            break
                    if not found:
                        all_dates.append((current_date, 0.0))
                    current_date += timedelta(days=1)
                    
                return all_dates
            return []
            
        except Exception as e:
            print(f"Error al obtener ventas diarias: {e}")
            return []

    def update_ganancias_chart(self):
        """Actualiza el gráfico de ganancias"""
        try:
            # Obtener datos de ventas y costos por receta
            recetas_data_raw = self.reportes_manager.obtener_ganancias_por_receta()
            
            # Calcular ganancia neta (ingresos - costos ingredientes - costos mano de obra)
            recetas_data = []
            for row in recetas_data_raw:
                nombre, cantidad_vendida, ingresos, costos_ingredientes, costos_mano_obra = row
                ganancia_neta = float(ingresos) - float(costos_ingredientes) - float(costos_mano_obra)
                recetas_data.append((nombre, cantidad_vendida, ingresos, ganancia_neta))
            
            # Preparar datos para el gráfico
            nombres = [r[0] for r in recetas_data]
            ganancias = [float(r[3]) for r in recetas_data]  # Ganancia neta
            
            # Limitar a las 10 recetas con mayores ganancias
            if len(nombres) > 10:
                nombres = nombres[:10]
                ganancias = ganancias[:10]
            
            # Limpiar gráfico anterior
            self.ax_ganancias.clear()
            
            # Crear gráfico de barras
            colors = ['#4CAF50' if g >= 0 else '#F44336' for g in ganancias]
            bars = self.ax_ganancias.bar(range(len(nombres)), ganancias, color=colors)
            self.ax_ganancias.set_title("Ganancias por Receta", fontsize=12, fontweight='bold')
            self.ax_ganancias.set_ylabel("Ganancia ($)")
            self.ax_ganancias.set_xlabel("Receta")
            
            # Etiquetas en el eje X
            self.ax_ganancias.set_xticks(range(len(nombres)))
            self.ax_ganancias.set_xticklabels(nombres, rotation=45, ha='right')
            
            # Añadir valores encima de las barras
            for i, (bar, ganancia) in enumerate(zip(bars, ganancias)):
                height = bar.get_height()
                self.ax_ganancias.text(bar.get_x() + bar.get_width()/2., height,
                        f'${ganancia:.2f}',
                        ha='center', va='bottom' if ganancia >= 0 else 'top')
            
            # Ajustar diseño
            self.fig_ganancias.tight_layout()
            
            # Actualizar canvas
            self.canvas_ganancias.draw()
            
        except Exception as e:
            print(f"Error al actualizar gráfico de ganancias: {e}")

    def obtener_datos_recetas(self):
        """Obtiene datos de ventas y costos por receta"""
        try:
            conn = self.reportes_manager.db_connection.get_connection()
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
            results = cursor.fetchall()
            cursor.close()
            
            # Calcular ganancia neta (ingresos - costos ingredientes - costos mano de obra)
            recetas_data = []
            for row in results:
                nombre, cantidad_vendida, ingresos, costos_ingredientes, costos_mano_obra = row
                ganancia_neta = float(ingresos) - float(costos_ingredientes) - float(costos_mano_obra)
                recetas_data.append((nombre, cantidad_vendida, ingresos, ganancia_neta))
                
            return recetas_data
            
        except Exception as e:
            print(f"Error al obtener datos de recetas: {e}")
            return []

    def update_productos_chart(self):
        """Actualiza el gráfico de productos más vendidos"""
        try:
            # Obtener productos más vendidos
            productos_data = self.reportes_manager.obtener_ventas_por_producto()
            
            # Preparar datos para el gráfico
            nombres = [p[0] for p in productos_data]
            cantidades = [p[1] for p in productos_data]
            
            # Limitar a los 10 productos más vendidos
            if len(nombres) > 10:
                nombres = nombres[:10]
                cantidades = cantidades[:10]
            
            # Limpiar gráfico anterior
            self.ax_productos.clear()
            
            # Crear gráfico de barras
            self.ax_productos.bar(nombres, cantidades, color='#FF9800')
            self.ax_productos.set_title("Productos Más Vendidos", fontsize=12, fontweight='bold')
            self.ax_productos.set_ylabel("Cantidad Vendida")
            self.ax_productos.set_xlabel("Producto")
            
            # Etiquetas en el eje X
            self.ax_productos.tick_params(axis='x', rotation=45)
            
            # Ajustar diseño
            self.fig_productos.tight_layout()
            
            # Actualizar canvas
            self.canvas_productos.draw()
            
        except Exception as e:
            print(f"Error al actualizar gráfico de productos: {e}")

    def obtener_productos_mas_vendidos(self):
        """Obtiene los productos más vendidos"""
        try:
            conn = self.reportes_manager.db_connection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.nombre, COALESCE(SUM(v.cantidad_vendida), 0) as total_vendido
                FROM recetas r
                LEFT JOIN ventas v ON r.id = v.producto_id
                GROUP BY r.id, r.nombre
                ORDER BY total_vendido DESC
                LIMIT 10
            """)
            results = cursor.fetchall()
            cursor.close()
            
            return results
            
        except Exception as e:
            print(f"Error al obtener productos más vendidos: {e}")
            return []
