import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter.font import Font
from Core.productos import Productos
from Core.UnitConverter import UnitConverter
from decimal import Decimal, InvalidOperation # Importar Decimal para manejo preciso

class GestionProductos(tk.Frame):
    def __init__(self, parent, productos_manager):
        super().__init__(parent)
        self.productos_manager = productos_manager
        self.unit_converter = UnitConverter()
        
        # Configurar fuentes modernas (ya definidas en styles.py, pero se pueden usar aquí si se desea sobrescribir)
        # self.font_title = Font(family="Helvetica", size=14, weight="bold")
        # self.font_body = Font(family="Arial", size=10)
        # self.font_button = Font(family="Arial", size=10, weight="bold")
        
        self._crear_widgets()
        self._configurar_layout()
        self.load_products() # Cargar productos al inicializar la página

    def _crear_widgets(self):
        """Crea todos los widgets con estilo moderno"""
        # Frame principal
        self.main_frame = ttk.Frame(self, style="TFrame") 
        
        # Título
        self.lbl_titulo = ttk.Label(
            self.main_frame, 
            text="GESTIÓN DE PRODUCTOS (MATERIAS PRIMAS)", # Texto más específico
            style="Titulo.TLabel"
        )
        
        # Treeview con scrollbar
        self.tree = ttk.Treeview(
            self.main_frame,
            columns=("ID", "Nombre", "Cantidad", "Unidad", "Costo Promedio", "Stock Mínimo", "Proveedor"), # Eliminada columna "Acción"
            show="headings",
            style="Modern.Treeview" # Usar el estilo Modern.Treeview
        )
        
        # Configurar encabezados y columnas
        column_config = [
            ("ID", 50, "center"),
            ("Nombre", 180, "w"),
            ("Cantidad", 100, "e"), # Cantidad alineada a la derecha
            ("Unidad", 80, "center"),
            ("Costo Promedio", 100, "e"), # Costo alineado a la derecha
            ("Stock Mínimo", 100, "e"), # Stock mínimo alineado a la derecha
            ("Proveedor", 150, "w")
        ]
        
        for col_name, width, anchor in column_config:
            self.tree.heading(col_name, text=col_name)
            self.tree.column(col_name, width=width, anchor=anchor)
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(
            self.main_frame,
            orient="vertical",
            command=self.tree.yview,
            style="Vertical.TScrollbar"
        )
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        # Frame para los botones de acción
        self.button_frame = ttk.Frame(self.main_frame, style="TFrame")
        
        # Botones
        self.btn_actualizar = ttk.Button(
            self.button_frame, # Poner en button_frame
            text="⟳ Actualizar Datos",
            style="Modern.TButton",
            command=self.load_products
        )
        
        self.btn_cambiar_unidad = ttk.Button(
            self.button_frame, # Poner en button_frame
            text="✏ Cambiar Unidad de Visualización",
            style="Modern.TButton",
            command=self.cambiar_unidad
        )
        
        self.btn_editar_stock_minimo = ttk.Button(
            self.button_frame, # Poner en button_frame
            text="⚙ Editar Stock Mínimo",
            style="Modern.TButton",
            command=self.editar_stock_minimo
        )

        self.btn_exportar = ttk.Button(
            self.button_frame, # Poner en button_frame
            text="📊 Exportar a CSV", # Cambiado a CSV por simplicidad
            style="Modern.TButton",
            command=self.exportar_csv # Cambiado a exportar_csv
        )

        self.btn_eliminar = ttk.Button(
            self.button_frame,
            text="🗑 Eliminar Producto",
            style="Danger.TButton",
            command=self.eliminar_producto
        )
        
        # Campo de búsqueda
        self.search_frame = ttk.Frame(self.main_frame, style="TFrame")
        ttk.Label(self.search_frame, text="Buscar Producto:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_search = ttk.Entry(self.search_frame, width=30, style="Modern.TEntry")
        self.entry_search.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_search.bind("<KeyRelease>", self._filter_products) # Filtrar al escribir

    def _configurar_layout(self):
        """Configura el layout usando grid"""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1) # El treeview ahora está en la fila 2

        self.lbl_titulo.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="w")

        self.search_frame.grid(row=1, column=0, columnspan=3, pady=(0, 10), sticky="ew") # Fila para búsqueda

        self.tree.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=(0, 5)) # Treeview en fila 2
        self.scrollbar.grid(row=2, column=2, sticky="ns") # Scrollbar en fila 2
        
        self.button_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0), sticky="ew") # Botones en fila 3
        
        # Layout de los botones dentro de button_frame
        self.button_frame.columnconfigure(0, weight=1) # Columna vacía para empujar botones a la derecha
        self.btn_actualizar.pack(side=tk.RIGHT, padx=5)
        self.btn_cambiar_unidad.pack(side=tk.RIGHT, padx=5)
        self.btn_editar_stock_minimo.pack(side=tk.RIGHT, padx=5)
        self.btn_exportar.pack(side=tk.RIGHT, padx=5)

    def load_products(self):
        """Carga los productos en el Treeview de forma segura."""
        try:
            # Limpiar el treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Obtener todos los productos
            productos = self.productos_manager.obtener_todos_los_productos()
            self.all_products_data = productos # Guardar todos los datos para filtrar
            
            if not productos:
                messagebox.showinfo("Información", "No hay productos registrados en el inventario.")
                return
                
            self._populate_treeview(productos)
                    
        except Exception as e:
            messagebox.showerror("Error de Carga", f"Error general al cargar productos: {str(e)}")

    def _populate_treeview(self, products_to_display):
        """Rellena el treeview con la lista de productos dada."""
        for prod in products_to_display:
            try:
                prod_id, nombre, cantidad_interna, unidad_interna, total_invertido, notas, stock_minimo, unidad_display, proveedor = prod
                
                # Calcular costo promedio
                costo_promedio = self.productos_manager.obtener_costo_promedio(prod_id)
                costo_promedio_fmt = f"${costo_promedio:.2f}"
                
                # Formatear cantidad para mostrar (convertir si unidad_interna != unidad_display)
                cantidad_para_mostrar = Decimal(str(cantidad_interna)) # Asegurar que sea Decimal
                try:
                    if unidad_interna != unidad_display and \
                       unidad_interna in self.unit_converter.CONVERSION_FACTORS and \
                       unidad_display in self.unit_converter.CONVERSION_FACTORS and \
                       self.unit_converter.UNIT_TYPES.get(unidad_interna) == self.unit_converter.UNIT_TYPES.get(unidad_display):
                        cantidad_para_mostrar = self.unit_converter.convert(cantidad_para_mostrar, unidad_interna, unidad_display)
                except Exception as e_conv:
                    # print(f"Advertencia: No se pudo convertir {cantidad_interna} {unidad_interna} a {unidad_display} para {nombre}. Error: {e_conv}")
                    pass # No mostrar error al usuario, solo usar la cantidad interna si falla la conversión

                cantidad_fmt = f"{cantidad_para_mostrar:.4f}" # Mostrar 4 decimales para precisión
                
                self.tree.insert("", "end", values=(
                    prod_id,
                    nombre,
                    cantidad_fmt,
                    unidad_display, # Mostrar la unidad de visualización
                    costo_promedio_fmt,
                    f"{stock_minimo:.4f}", # Mostrar stock mínimo con 4 decimales
                    proveedor if proveedor else "N/A"
                ))
            except Exception as e_prod:
                print(f"Error al procesar producto {prod}: {str(e_prod)}")
                # messagebox.showerror("Error de Carga", f"Error al procesar un producto: {str(e_prod)}") # Demasiado intrusivo

    def _filter_products(self, event=None):
        """Filtra los productos en el Treeview según el texto de búsqueda."""
        search_term = self.entry_search.get().strip().lower()
        
        # Limpiar el treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not search_term:
            # Si el campo de búsqueda está vacío, mostrar todos los productos
            self._populate_treeview(self.all_products_data)
        else:
            # Filtrar los productos
            filtered_products = [
                p for p in self.all_products_data 
                if search_term in p[1].lower() # Buscar por nombre de producto
            ]
            self._populate_treeview(filtered_products)

    def editar_stock_minimo(self):
        """Método para editar el stock mínimo de un producto."""
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un producto primero para editar su stock mínimo.")
            return
            
        item = self.tree.item(selected)
        prod_id = item['values'][0]
        nombre_producto = item['values'][1]
        stock_minimo_actual_str = item['values'][5] # Stock mínimo actual como string
        
        # Diálogo para editar stock mínimo
        nuevo_stock_minimo_str = simpledialog.askstring(
            "Editar Stock Mínimo",
            f"Ingrese el nuevo stock mínimo para '{nombre_producto}':",
            initialvalue=stock_minimo_actual_str
        )
        
        if nuevo_stock_minimo_str is None: # Usuario canceló
            return
            
        try:
            nuevo_stock_minimo = Decimal(nuevo_stock_minimo_str)
            if nuevo_stock_minimo < Decimal('0'):
                raise ValueError("El stock mínimo no puede ser negativo.")
            
            # Iniciar transacción para la actualización
            self.productos_manager.db_connection.get_connection().start_transaction()
            success = self.productos_manager.actualizar_stock_minimo(prod_id, nuevo_stock_minimo)
            self.productos_manager.db_connection.commit() # Confirmar la transacción
            
            if success:
                messagebox.showinfo("Éxito", f"Stock mínimo de '{nombre_producto}' actualizado correctamente a {nuevo_stock_minimo:.4f}.")
                self.load_products()  # Refrescar vista
            else:
                messagebox.showerror("Error", "No se pudo actualizar el stock mínimo en la base de datos.")
        except InvalidOperation:
            messagebox.showerror("Error de Entrada", "Ingrese un valor numérico válido para el stock mínimo.")
        except ValueError as ve:
            messagebox.showerror("Error de Validación", str(ve))
        except Exception as e:
            self.productos_manager.db_connection.rollback() # Revertir en caso de error
            messagebox.showerror("Error", f"Ocurrió un error al actualizar el stock mínimo: {str(e)}")

    def cambiar_unidad(self):
        """Método para cambiar la unidad de visualización de un producto."""
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un producto primero para cambiar su unidad de visualización.")
            return
            
        item = self.tree.item(selected)
        prod_id = item['values'][0]
        nombre_producto = item['values'][1]
        unidad_actual_display = item['values'][3] # Unidad de visualización actual
        
        # Obtener la unidad base del producto para filtrar unidades compatibles
        try:
            producto_data = self.productos_manager.obtener_producto(prod_id)
            if not producto_data:
                messagebox.showerror("Error", "No se pudo obtener la información del producto.")
                return
            unidad_base_interna = producto_data[3] # 'unidad' en la tabla productos
            
            # Obtener el tipo de magnitud de la unidad base interna
            unit_type = self.unit_converter.UNIT_TYPES.get(unidad_base_interna)
            if not unit_type:
                messagebox.showerror("Error de Unidad", f"La unidad base interna '{unidad_base_interna}' del producto '{nombre_producto}' no tiene un tipo de magnitud definido. No se puede cambiar la unidad de visualización.")
                return
            
            # Obtener solo las unidades compatibles con el tipo de magnitud de la unidad base
            unidades_compatibles = self.unit_converter.get_units_by_type(unit_type)
            if not unidades_compatibles:
                messagebox.showwarning("Advertencia", f"No hay unidades compatibles definidas para el tipo '{unit_type}'.")
                return

        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener unidades compatibles: {str(e)}")
            return

        # Diálogo para cambiar unidad
        dialog = tk.Toplevel(self)
        dialog.title("Cambiar Unidad de Visualización")
        dialog.transient(self.master) # Hacer que el diálogo sea modal
        dialog.geometry("350x180")
        dialog.resizable(False, False)
        
        # Update the window to ensure it's fully created before calling grab_set
        dialog.update_idletasks()
        dialog.grab_set() # Capturar eventos
        
        tk.Label(dialog, text=f"Producto: {nombre_producto}", font=("Segoe UI", 10, "bold")).pack(pady=5)
        ttk.Label(dialog, text="Seleccione la nueva unidad de visualización:").pack(pady=5)
        
        unidad_var = tk.StringVar(value=unidad_actual_display)
        combo = ttk.Combobox(dialog, textvariable=unidad_var, values=unidades_compatibles, state="readonly", style="Modern.TCombobox")
        combo.pack(pady=5)
        
        # Botones
        btn_frame = ttk.Frame(dialog, style="TFrame")
        btn_frame.pack(pady=10)
        
        ttk.Button(
            btn_frame,
            text="Aceptar",
            style="Accent.TButton", # Usar estilo Accent
            command=lambda: self.actualizar_unidad_display_db(prod_id, unidad_var.get(), dialog)
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancelar",
            style="Modern.TButton",
            command=dialog.destroy
        ).pack(side="left", padx=5)

        self.master.wait_window(dialog) # Esperar a que el diálogo se cierre

    def actualizar_unidad_display_db(self, product_id: int, nueva_unidad_display: str, dialog: tk.Toplevel):
        """Actualiza la unidad de visualización en la base de datos."""
        if not nueva_unidad_display:
            messagebox.showwarning("Error", "Seleccione una unidad válida.")
            return
            
        try:
            # Iniciar transacción para la actualización
            self.productos_manager.db_connection.get_connection().start_transaction()
            success = self.productos_manager.actualizar_unidad_display(product_id, nueva_unidad_display)
            self.productos_manager.db_connection.commit() # Confirmar la transacción
            
            if success:
                messagebox.showinfo("Éxito", f"Unidad de visualización actualizada correctamente a '{nueva_unidad_display}'.")
                dialog.destroy()
                self.load_products()  # Refrescar vista
            else:
                messagebox.showerror("Error", "No se pudo actualizar la unidad de visualización en la base de datos.")
        except Exception as e:
            self.productos_manager.db_connection.rollback() # Revertir en caso de error
            messagebox.showerror("Error", f"Ocurrió un error al actualizar la unidad: {str(e)}")

    def exportar_csv(self):
        """Exporta los datos del Treeview a un archivo CSV."""
        from tkinter import filedialog
        import csv

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Guardar Reporte de Productos"
        )
        
        if not file_path:
            return # Usuario canceló

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Escribir encabezados
                headers = [self.tree.heading(col)['text'] for col in self.tree['columns']]
                writer.writerow(headers)
                
                # Escribir datos
                for item_id in self.tree.get_children():
                    row_values = self.tree.item(item_id)['values']
                    writer.writerow(row_values)
            
            messagebox.showinfo("Éxito", f"Datos exportados a:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"No se pudo exportar el archivo CSV: {str(e)}")

    def eliminar_producto(self):
        """Maneja la eliminación de un producto seleccionado."""
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un producto primero para eliminar.")
            return
        
        item = self.tree.item(selected)
        prod_id = item['values'][0]
        nombre_producto = item['values'][1]

        confirm = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro que desea eliminar el producto '{nombre_producto}'?\n\nEsta acción no se puede deshacer."
        )
        
        if not confirm:
            return

        try:
            # Iniciar transacción para la eliminación
            self.productos_manager.db_connection.get_connection().start_transaction()
            success = self.productos_manager.eliminar_producto(prod_id)
            self.productos_manager.db_connection.commit()
            
            if success:
                messagebox.showinfo("Éxito", f"Producto '{nombre_producto}' eliminado correctamente.")
                self.load_products()  # Refrescar la lista de productos
            else:
                messagebox.showerror("Error", "No se pudo eliminar el producto.")
                
        except Exception as e:
            self.productos_manager.db_connection.rollback()
            messagebox.showerror("Error", f"Error al eliminar el producto: {str(e)}")

        prod_id = item['values'][0]
        nombre_producto = item['values'][1]

        confirm = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro que desea eliminar el producto '{nombre_producto}'?\n\nEsta acción no se puede deshacer."
        )
        