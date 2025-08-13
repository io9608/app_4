import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal, InvalidOperation
from Core.productos import Productos
from Core.recetas import RecetasManager
from Core.UnitConverter import UnitConverter

# --- Clase de Diálogo Personalizado para Cantidad y Unidad ---
class CantidadUnidadDialog(simpledialog.Dialog):
    def __init__(self, parent, title, default_unit, unit_type, unit_converter, initial_quantity=None):
        self.default_unit = default_unit
        self.unit_type = unit_type
        self.unit_converter = unit_converter
        self.selected_unit = tk.StringVar(value=default_unit)
        self.initial_quantity = initial_quantity
        self.result_cantidad = None
        self.result_unidad = None

        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Cantidad:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_cantidad = ttk.Entry(master, style="Modern.TEntry")
        self.entry_cantidad.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.entry_cantidad.insert(0, str(self.initial_quantity) if self.initial_quantity is not None else "1.0") # Valor inicial
        self.entry_cantidad.focus_set()

        tk.Label(master, text="Unidad:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        compatible_units = self.unit_converter.get_units_by_type(self.unit_type)
        
        self.combo_unidad = ttk.Combobox(master, textvariable=self.selected_unit, 
                                         values=compatible_units, state="readonly", style="Modern.TCombobox")
        self.combo_unidad.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        if self.default_unit in compatible_units:
            self.combo_unidad.set(self.default_unit)
        elif compatible_units:
            self.combo_unidad.set(compatible_units[0])
        else:
            self.combo_unidad.set("N/A")
            self.combo_unidad.config(state="disabled")

        master.grid_columnconfigure(1, weight=1) # Permitir que la columna de entrada se expanda
        return self.entry_cantidad

    def buttonbox(self):
        box = ttk.Frame(self)
        
        w = ttk.Button(box, text="OK", width=10, command=self.ok, default="active", style="Accent.TButton")
        w.pack(side="left", padx=5, pady=5)
        w = ttk.Button(box, text="Cancel", width=10, command=self.cancel, style="Modern.TButton")
        w.pack(side="left", padx=5, pady=5)
        
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        
        box.pack()

    def apply(self):
        try:
            cantidad_str = self.entry_cantidad.get().strip()
            unidad_str = self.selected_unit.get().strip()

            if not cantidad_str:
                raise ValueError("La cantidad no puede estar vacía.")
            
            self.result_cantidad = Decimal(cantidad_str)
            self.result_unidad = unidad_str

            if self.result_cantidad <= Decimal('0'):
                raise ValueError("La cantidad debe ser un número positivo.")
            if not self.result_unidad or self.result_unidad == "N/A":
                raise ValueError("Debe seleccionar una unidad válida.")
        except InvalidOperation:
            messagebox.showerror("Entrada inválida", "Por favor, ingrese una cantidad numérica válida.")
            self.result_cantidad = None
            self.result_unidad = None
        except ValueError as e:
            messagebox.showerror("Entrada inválida", f"Error: {e}")
            self.result_cantidad = None
            self.result_unidad = None
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}")
            self.result_cantidad = None
            self.result_unidad = None


# --- Modificaciones en la clase RecetasEditor ---
class RecetasEditor(tk.Frame):
    def __init__(self, parent, productos_manager, recetas_manager):
        super().__init__(parent)
        self.productos_manager = productos_manager
        self.recetas_manager = recetas_manager
        self.unit_converter = UnitConverter()
        self.ingredientes_en_receta = [] # Almacena (ingrediente_id, nombre, cantidad, unidad, costo_promedio_ingrediente)
        self.current_editing_receta_id = None # Para saber qué receta se está editando
        self.trabajadores_temporales = [] # Almacena (id, nombre_trabajador, pago) para trabajadores nuevos

        self.create_widgets()
        self.load_productos_base()
        self.load_recetas_existentes() # Cargar recetas existentes al inicio
        
    def create_widgets(self):
        # Panel principal con notebook
        self.notebook = ttk.Notebook(self, style="TNotebook") # Aplicar estilo
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña 1: Editor de recetas
        self.editor_frame = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.editor_frame, text="Editor de Recetas")
        
        # --- Sección de Creación de Receta ---
        receta_info_frame = ttk.LabelFrame(self.editor_frame, text="Información de la Receta", style="Card.TFrame") # Aplicar estilo
        receta_info_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(receta_info_frame, text="Nombre de la Receta:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.entry_nombre_receta = ttk.Entry(receta_info_frame, width=40, style="Modern.TEntry") # Aplicar estilo
        self.entry_nombre_receta.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(receta_info_frame, text="Categoría:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.combo_categoria = ttk.Combobox(receta_info_frame, values=["COMIDAS", "JUGOS", "POSTRES", "OTROS"], state="readonly", style="Modern.TCombobox") # Aplicar estilo
        self.combo_categoria.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.combo_categoria.set("COMIDAS") # Valor por defecto

        ttk.Label(receta_info_frame, text="Precio de Venta ($):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.entry_precio_venta = ttk.Entry(receta_info_frame, width=15, style="Modern.TEntry") # Aplicar estilo
        self.entry_precio_venta.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        self.entry_precio_venta.insert(0, "0.00")

        # Sección de Trabajadores
        trabajadores_frame = ttk.LabelFrame(receta_info_frame, text="Trabajadores", style="Card.TFrame")
        trabajadores_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        trabajadores_frame.columnconfigure(1, weight=1)

        # Campos para agregar trabajadores
        ttk.Label(trabajadores_frame, text="Nombre Trabajador:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.entry_nombre_trabajador = ttk.Entry(trabajadores_frame, width=20, style="Modern.TEntry")
        self.entry_nombre_trabajador.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(trabajadores_frame, text="Pago ($):").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.entry_pago_trabajador = ttk.Entry(trabajadores_frame, width=10, style="Modern.TEntry")
        self.entry_pago_trabajador.grid(row=0, column=3, padx=5, pady=2)
        self.entry_pago_trabajador.insert(0, "0.00")

        ttk.Button(trabajadores_frame, text="➕ Agregar Trabajador", 
                  command=self.agregar_trabajador, style="Modern.TButton").grid(row=0, column=4, padx=5, pady=2)

        # Treeview para mostrar trabajadores
        self.tree_trabajadores = ttk.Treeview(trabajadores_frame, 
                                            columns=('id', 'nombre', 'pago'),
                                            show='headings', style="Modern.Treeview", height=4)
        self.tree_trabajadores.heading('id', text='ID')
        self.tree_trabajadores.heading('nombre', text='Nombre Trabajador')
        self.tree_trabajadores.heading('pago', text='Pago ($)')
        self.tree_trabajadores.column('id', width=40, anchor='center')
        self.tree_trabajadores.column('nombre', width=150, anchor='w')
        self.tree_trabajadores.column('pago', width=80, anchor='e')
        self.tree_trabajadores.grid(row=1, column=0, columnspan=5, sticky="nsew", padx=5, pady=5)

        # Scrollbar para tree_trabajadores
        trabajadores_scrollbar = ttk.Scrollbar(trabajadores_frame, orient="vertical", command=self.tree_trabajadores.yview)
        trabajadores_scrollbar.grid(row=1, column=5, sticky="ns")
        self.tree_trabajadores.configure(yscrollcommand=trabajadores_scrollbar.set)

        # Botón para eliminar trabajador
        ttk.Button(trabajadores_frame, text="➖ Eliminar Trabajador", 
                  command=self.eliminar_trabajador, style="Modern.TButton").grid(row=2, column=0, columnspan=5, pady=5)

        trabajadores_frame.rowconfigure(1, weight=1)
        trabajadores_frame.columnconfigure(1, weight=1)

        receta_info_frame.grid_columnconfigure(1, weight=1) # Permitir expansión

        # Contenedor para los dos Treeviews y los controles
        content_frame = ttk.Frame(self.editor_frame, style="TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_columnconfigure(2, weight=0) # Controles no se expanden
        content_frame.grid_rowconfigure(0, weight=1)

        # Panel izquierdo (ingredientes disponibles)
        self.ingredientes_frame = ttk.LabelFrame(content_frame, text="Inventario de Materias Primas", style="Card.TFrame") # Aplicar estilo
        self.ingredientes_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.tree_ingredientes = ttk.Treeview(self.ingredientes_frame, columns=('id', 'nombre', 'stock', 'unidad'), show='headings', style="Modern.Treeview") # Aplicar estilo
        self.tree_ingredientes.heading('id', text='ID')
        self.tree_ingredientes.heading('nombre', text='Materia Prima')
        self.tree_ingredientes.heading('stock', text='Disponible')
        self.tree_ingredientes.heading('unidad', text='Unidad')
        self.tree_ingredientes.column('id', width=40, anchor='center')
        self.tree_ingredientes.column('nombre', width=150, anchor='w')
        self.tree_ingredientes.column('stock', width=80, anchor='e')
        self.tree_ingredientes.column('unidad', width=60, anchor='center')
        self.tree_ingredientes.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar para tree_ingredientes
        ingredientes_scrollbar = ttk.Scrollbar(self.ingredientes_frame, orient="vertical", command=self.tree_ingredientes.yview, style="Vertical.TScrollbar")
        ingredientes_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.tree_ingredientes.configure(yscrollcommand=ingredientes_scrollbar.set)

        # Panel central (receta actual)
        self.receta_frame = ttk.LabelFrame(content_frame, text="Ingredientes de la Receta", style="Card.TFrame") # Aplicar estilo
        self.receta_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.tree_receta = ttk.Treeview(self.receta_frame, 
                                      columns=('id', 'nombre', 'cantidad', 'costo_parcial'),
                                      show='headings', style="Modern.Treeview") # Aplicar estilo
        self.tree_receta.heading('id', text='ID')
        self.tree_receta.heading('nombre', text='Ingrediente')
        self.tree_receta.heading('cantidad', text='Cantidad')
        self.tree_receta.heading('costo_parcial', text='Costo Parcial')
        self.tree_receta.column('id', width=40, anchor='center')
        self.tree_receta.column('nombre', width=150, anchor='w')
        self.tree_receta.column('cantidad', width=100, anchor='e')
        self.tree_receta.column('costo_parcial', width=80, anchor='e')
        self.tree_receta.pack(fill=tk.BOTH, expand=True)

        # Scrollbar para tree_receta
        receta_scrollbar = ttk.Scrollbar(self.receta_frame, orient="vertical", command=self.tree_receta.yview, style="Vertical.TScrollbar")
        receta_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.tree_receta.configure(yscrollcommand=receta_scrollbar.set)
        
        # Panel derecho (controles y resumen)
        self.controls_frame = ttk.Frame(content_frame, style="TFrame")
        self.controls_frame.grid(row=0, column=2, sticky="ns", padx=5, pady=5)
        
        # Visualización de costo total
        ttk.Label(self.controls_frame, text="Costo Total de Ingredientes:", font=("Segoe UI", 10, "bold")).pack(pady=(0, 5))
        self.costo_total_var = tk.StringVar(value="$0.00")
        ttk.Label(self.controls_frame, textvariable=self.costo_total_var, 
                 font=('Helvetica', 12, 'bold'), foreground="blue").pack(pady=(0, 15))
        
        # Botones de acción
        ttk.Button(self.controls_frame, text="➕ Agregar a Receta", 
                  command=self.agregar_ingrediente_a_receta, style="Modern.TButton").pack(pady=5, fill=tk.X)
        ttk.Button(self.controls_frame, text="➖ Eliminar de Receta", 
                  command=self.eliminar_ingrediente_de_receta, style="Modern.TButton").pack(pady=5, fill=tk.X)
        
        # Botón Guardar/Actualizar Receta
        self.btn_guardar_actualizar = ttk.Button(self.controls_frame, text="💾 Guardar Receta", 
                                                 command=self.guardar_receta, style="Accent.TButton")
        self.btn_guardar_actualizar.pack(pady=(15, 5), fill=tk.X)
        
        ttk.Button(self.controls_frame, text="🧹 Limpiar Formulario", 
                  command=self.limpiar_formulario, style="Modern.TButton").pack(pady=5, fill=tk.X)
        
        # Pestaña 2: Listado de recetas existentes (ahora con control de costos)
        self.listado_frame = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.listado_frame, text="Recetas Existentes y Control de Costos") # Nuevo título
        
        # Controles de búsqueda y actualización para recetas existentes
        listado_controls_frame = ttk.Frame(self.listado_frame, style="TFrame")
        listado_controls_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(listado_controls_frame, text="Buscar Receta:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_search_recetas = ttk.Entry(listado_controls_frame, width=30, style="Modern.TEntry")
        self.entry_search_recetas.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_search_recetas.bind("<KeyRelease>", self._filter_recetas_existentes)

        ttk.Button(listado_controls_frame, text="⟳ Actualizar Lista", command=self.load_recetas_existentes, style="Modern.TButton").pack(side=tk.RIGHT, padx=5)

        # Configuración del treeview de recetas existentes
        self.tree_recetas_existentes = ttk.Treeview(self.listado_frame, 
                                        columns=('id', 'nombre', 'categoria', 'costo_ingredientes', 'costo_mano_obra', 'precio_venta', 'ganancia'),
                                        show='headings', style="Modern.Treeview")
        self.tree_recetas_existentes.heading('id', text='ID')
        self.tree_recetas_existentes.heading('nombre', text='Receta')
        self.tree_recetas_existentes.heading('categoria', text='Categoría')
        self.tree_recetas_existentes.heading('costo_ingredientes', text='Costo Ingredientes ($)')
        self.tree_recetas_existentes.heading('costo_mano_obra', text='Costo M.O. ($)')
        self.tree_recetas_existentes.heading('precio_venta', text='Precio Venta ($)')
        self.tree_recetas_existentes.heading('ganancia', text='Ganancia ($)')

        self.tree_recetas_existentes.column('id', width=40, anchor='center')
        self.tree_recetas_existentes.column('nombre', width=150, anchor='w')
        self.tree_recetas_existentes.column('categoria', width=100, anchor='center')
        self.tree_recetas_existentes.column('costo_ingredientes', width=120, anchor='e')
        self.tree_recetas_existentes.column('costo_mano_obra', width=100, anchor='e')
        self.tree_recetas_existentes.column('precio_venta', width=100, anchor='e')
        self.tree_recetas_existentes.column('ganancia', width=100, anchor='e')

        self.tree_recetas_existentes.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar para tree_recetas_existentes
        recetas_existentes_scrollbar = ttk.Scrollbar(self.listado_frame, orient="vertical", command=self.tree_recetas_existentes.yview, style="Vertical.TScrollbar")
        recetas_existentes_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.tree_recetas_existentes.configure(yscrollcommand=recetas_existentes_scrollbar.set)

        # Botones de acción para recetas existentes
        recetas_action_frame = ttk.Frame(self.listado_frame, style="TFrame")
        recetas_action_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(recetas_action_frame, text="✏ Editar Receta Seleccionada", command=self.editar_receta_existente, style="Modern.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(recetas_action_frame, text="🗑 Eliminar Receta Seleccionada", command=self.eliminar_receta_existente, style="Modern.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(recetas_action_frame, text="📊 Exportar Recetas a CSV", command=self.exportar_recetas_csv, style="Modern.TButton").pack(side=tk.RIGHT, padx=5)

        # Configurar eventos
        self.tree_ingredientes.bind('<Double-1>', self.agregar_ingrediente_a_receta)
        self.tree_receta.bind('<Delete>', self.eliminar_ingrediente_de_receta) # Permite eliminar con tecla Supr
        self.tree_receta.bind('<Double-1>', self.editar_cantidad_ingrediente) # Editar cantidad de ingrediente en receta
        
        # Eventos para edición directa en el Treeview de recetas existentes
        self.tree_recetas_existentes.bind("<Double-1>", self.on_double_click_recetas_existentes)

    def load_productos_base(self):
        """Carga las materias primas disponibles en el Treeview de inventario."""
        for item in self.tree_ingredientes.get_children():
            self.tree_ingredientes.delete(item)
        
        try:
            productos = self.productos_manager.obtener_todos_los_productos()
            for p in productos:
                # p: (id, nombre_producto, cantidad, unidad, total_invertido, notas, stock_minimo, unidad_display, proveedor)
                prod_id, nombre, cantidad, unidad_interna, total_invertido, _, _, unidad_display, _ = p
                
                costo_promedio = self.productos_manager.obtener_costo_promedio(prod_id)

                self.tree_ingredientes.insert('', 'end', 
                                            values=(prod_id, nombre, f"{float(cantidad):.4f} {unidad_display}", unidad_display),
                                            tags=(str(prod_id), str(costo_promedio), unidad_interna)) # Guardamos ID, costo_promedio y unidad_interna en tags
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar las materias primas: {str(e)}")
    
    def agregar_ingrediente_a_receta(self, event=None):
        """Agrega el ingrediente seleccionado del inventario a la receta en edición."""
        seleccion = self.tree_ingredientes.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Seleccione una materia prima del inventario para agregar.")
            return
        
        item = self.tree_ingredientes.item(seleccion)
        ingrediente_id = item['values'][0]
        nombre_ingrediente = item['values'][1]
        unidad_display_producto = item['values'][3] # Unidad de display del producto
        costo_promedio_ingrediente = Decimal(item['tags'][1]) # Costo promedio guardado en tags
        unidad_interna_base_ingrediente = item['tags'][2] # Unidad interna base del producto

        unit_type = self.unit_converter.UNIT_TYPES.get(unidad_interna_base_ingrediente) # Usar unidad_interna_base para el tipo
        if not unit_type:
            messagebox.showerror("Error de Unidad", f"La unidad base interna '{unidad_interna_base_ingrediente}' del producto '{nombre_ingrediente}' no tiene un tipo de magnitud definido en UnitConverter. No se puede añadir.")
            return

        # Verificar si el ingrediente ya está en la receta para obtener la cantidad actual
        current_quantity = None
        current_unit = None
        for i, (existing_id, _, existing_quantity, existing_unit, _) in enumerate(self.ingredientes_en_receta):
            if existing_id == ingrediente_id:
                current_quantity = existing_quantity
                current_unit = existing_unit
                break

        dialog = CantidadUnidadDialog(self, 
                                      f"Cantidad de {nombre_ingrediente}", 
                                      current_unit if current_unit else unidad_display_producto, # Unidad por defecto
                                      unit_type, 
                                      self.unit_converter,
                                      initial_quantity=current_quantity)
        
        cantidad = dialog.result_cantidad
        unidad_elegida = dialog.result_unidad

        if cantidad is None or unidad_elegida is None: # Usuario canceló o validación falló en el diálogo
            return
        
        # Actualizar o añadir a la lista temporal de ingredientes de la receta
        if current_quantity is not None:
            # Actualizar cantidad y unidad si ya existe
            for i, (existing_id, _, _, _, _) in enumerate(self.ingredientes_en_receta):
                if existing_id == ingrediente_id:
                    self.ingredientes_en_receta[i] = (ingrediente_id, nombre_ingrediente, cantidad, unidad_elegida, costo_promedio_ingrediente)
                    break
        else:
            # Añadir nuevo ingrediente
            self.ingredientes_en_receta.append((ingrediente_id, nombre_ingrediente, cantidad, unidad_elegida, costo_promedio_ingrediente))
        
        self.actualizar_treeview_receta()
        self.calcular_costo_total_receta()
        messagebox.showinfo("Ingrediente Agregado/Actualizado", f"'{nombre_ingrediente}' agregado/actualizado en la receta a {cantidad:.4f} {unidad_elegida}.")
    
    def editar_cantidad_ingrediente(self, event=None):
        """Permite editar la cantidad de un ingrediente ya en la receta."""
        seleccion = self.tree_receta.selection()
        if not seleccion:
            return # No hay nada seleccionado
        
        item = self.tree_receta.item(seleccion)
        ingrediente_id = item['values'][0]
        nombre_ingrediente = item['values'][1]
        cantidad_actual_str = item['values'][2].split(' ')[0] # "10.0000 kg" -> "10.0000"
        unidad_actual = item['values'][2].split(' ')[1] # "10.0000 kg" -> "kg"

        # Obtener la unidad base interna del producto para el tipo de magnitud
        try:
            producto_data = self.productos_manager.obtener_producto(ingrediente_id)
            if not producto_data:
                messagebox.showerror("Error", "No se pudo obtener la información del ingrediente.")
                return
            unidad_base_interna = producto_data[3]
            unit_type = self.unit_converter.UNIT_TYPES.get(unidad_base_interna)
            if not unit_type:
                messagebox.showerror("Error de Unidad", f"La unidad base interna '{unidad_base_interna}' del ingrediente '{nombre_ingrediente}' no tiene un tipo de magnitud definido. No se puede editar.")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener tipo de unidad: {str(e)}")
            return

        dialog = CantidadUnidadDialog(self, 
                                      f"Editar Cantidad de {nombre_ingrediente}", 
                                      unidad_actual, 
                                      unit_type, 
                                      self.unit_converter,
                                      initial_quantity=Decimal(cantidad_actual_str))
        
        cantidad_nueva = dialog.result_cantidad
        unidad_nueva = dialog.result_unidad

        if cantidad_nueva is None or unidad_nueva is None:
            return # Usuario canceló o validación falló

        # Actualizar la lista temporal
        for i, (ing_id, nombre, _, _, costo_promedio) in enumerate(self.ingredientes_en_receta):
            if ing_id == ingrediente_id:
                self.ingredientes_en_receta[i] = (ing_id, nombre, cantidad_nueva, unidad_nueva, costo_promedio)
                break
        
        self.actualizar_treeview_receta()
        self.calcular_costo_total_receta()
        messagebox.showinfo("Actualizado", f"Cantidad de '{nombre_ingrediente}' actualizada a {cantidad_nueva:.4f} {unidad_nueva}.")

    def eliminar_ingrediente_de_receta(self, event=None):
        """Elimina un ingrediente seleccionado de la receta en edición."""
        seleccion = self.tree_receta.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Seleccione un ingrediente de la receta para eliminar.")
            return
        
        item = self.tree_receta.item(seleccion)
        ingrediente_id_a_eliminar = item['values'][0] 
        nombre_ingrediente = item['values'][1]

        if not messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar '{nombre_ingrediente}' de la receta?"):
            return

        self.ingredientes_en_receta = [
            ing for ing in self.ingredientes_en_receta 
            if ing[0] != ingrediente_id_a_eliminar
        ]
        self.actualizar_treeview_receta()
        self.calcular_costo_total_receta()
        messagebox.showinfo("Eliminado", f"Ingrediente '{nombre_ingrediente}' eliminado de la receta.")

    def actualizar_treeview_receta(self):
        """Actualiza el Treeview de la receta con los ingredientes temporales."""
        for item in self.tree_receta.get_children():
            self.tree_receta.delete(item)
        
        for ing_id, nombre, cantidad_receta, unidad_receta, costo_promedio_ingrediente in self.ingredientes_en_receta:
            producto_data = self.productos_manager.obtener_producto(ing_id)
            costo_parcial = Decimal('0.00')
            if producto_data:
                unidad_base_ingrediente = producto_data[3] # 'unidad' en la tabla productos
                try:
                    cantidad_en_base = self.unit_converter.convert(
                        cantidad_receta, unidad_receta, unidad_base_ingrediente
                    )
                    costo_parcial = cantidad_en_base * costo_promedio_ingrediente
                except Exception as e:
                    print(f"Error al calcular costo parcial para {nombre}: {e}")
                    # No mostrar messagebox aquí, solo en el cálculo total o al guardar
            else:
                print(f"Advertencia: Producto ID {ing_id} no encontrado para calcular costo parcial en GUI.")

            self.tree_receta.insert('', 'end', values=(ing_id, nombre, f"{cantidad_receta:.4f} {unidad_receta}", f"${costo_parcial:.2f}"))

    def calcular_costo_total_receta(self):
        """Calcula y actualiza el costo total mostrado de la receta."""
        total = Decimal('0.00')
        for ing_id, _, cantidad_receta, unidad_receta, costo_promedio_ingrediente in self.ingredientes_en_receta:
            producto_data = self.productos_manager.obtener_producto(ing_id)
            if producto_data:
                unidad_base_ingrediente = producto_data[3]
                try:
                    cantidad_en_base = self.unit_converter.convert(
                        cantidad_receta, unidad_receta, unidad_base_ingrediente
                    )
                    total += cantidad_en_base * costo_promedio_ingrediente
                except Exception as e:
                    print(f"Error al calcular costo total para ingrediente {ing_id}: {e}")
            else:
                print(f"Advertencia: Producto ID {ing_id} no encontrado para calcular costo total.")

        self.costo_total_var.set(f"${total:.2f}")
    
    def guardar_receta(self):
        """Guarda la receta actual y sus ingredientes en la base de datos."""
        nombre_receta = self.entry_nombre_receta.get().strip()
        categoria = self.combo_categoria.get()
        precio_venta_str = self.entry_precio_venta.get().strip()

        if not nombre_receta:
            messagebox.showerror("Error", "El nombre de la receta no puede estar vacío.")
            return
        if not self.ingredientes_en_receta:
            messagebox.showerror("Error", "La receta debe contener al menos un ingrediente.")
            return
        
        try:
            precio_venta = Decimal(precio_venta_str)
            if precio_venta < Decimal('0'):
                raise ValueError("El precio de venta no puede ser negativo.")

            # Calcular costo total de mano de obra de los trabajadores
            costo_mano_obra_total = Decimal('0.00')
            for _, _, pago in self.trabajadores_temporales:
                costo_mano_obra_total += pago

            # Iniciar la transacción
            self.recetas_manager.db_connection.get_connection().start_transaction()

            # Crear la receta principal
            receta_id = self.recetas_manager.crear_receta(nombre_receta, categoria, precio_venta, costo_mano_obra_total)
            
            # Añadir cada ingrediente a la receta
            for ing_id, _, cantidad, unidad, _ in self.ingredientes_en_receta:
                self.recetas_manager.agregar_ingrediente_a_receta(receta_id, ing_id, cantidad, unidad)
            
            # Guardar trabajadores
            self.guardar_trabajadores_de_receta(receta_id)
            
            self.recetas_manager.db_connection.commit() # Confirmar la transacción
            messagebox.showinfo("Éxito", f"Receta '{nombre_receta}' guardada correctamente con ID: {receta_id}")
            self.limpiar_formulario()
            self.load_recetas_existentes() # Recargar la lista de recetas existentes
            
        except InvalidOperation:
            self.recetas_manager.db_connection.rollback()
            messagebox.showerror("Error de Entrada", "Ingrese valores numéricos válidos para Precio de Venta.")
        except ValueError as ve:
            self.recetas_manager.db_connection.rollback()
            messagebox.showerror("Error de Validación", str(ve))
        except Exception as e:
            self.recetas_manager.db_connection.rollback()
            messagebox.showerror("Error", f"No se pudo guardar la receta: {str(e)}")
    
    def limpiar_formulario(self):
        """Limpia todos los campos del editor después de guardar."""
        self.entry_nombre_receta.delete(0, tk.END)
        self.combo_categoria.set("COMIDAS")
        self.entry_precio_venta.delete(0, tk.END)
        self.entry_precio_venta.insert(0, "0.00")
        self.entry_nombre_trabajador.delete(0, tk.END)
        self.entry_pago_trabajador.delete(0, tk.END)
        self.entry_pago_trabajador.insert(0, "0.00")
        self.ingredientes_en_receta = []
        self.trabajadores_temporales = []
        self.actualizar_treeview_receta()
        self.actualizar_treeview_trabajadores()
        self.costo_total_var.set("$0.00")
        self.load_productos_base() # Recargar inventario por si hubo cambios
        self.current_editing_receta_id = None # Resetear ID de edición
        self.btn_guardar_actualizar.config(text="💾 Guardar Receta", command=self.guardar_receta) # Restaurar botón

    def load_recetas_existentes(self):
        """Carga las recetas existentes en el Treeview de la segunda pestaña."""
        for item in self.tree_recetas_existentes.get_children():
            self.tree_recetas_existentes.delete(item)
        
        try:
            recetas = self.recetas_manager.obtener_todas_las_recetas()
            self.all_recetas_data = recetas # Guardar para filtrar
            
            if not recetas:
                # messagebox.showinfo("Información", "No hay recetas registradas.") # Demasiado intrusivo
                return

            self._populate_recetas_treeview(recetas)

        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar las recetas existentes: {str(e)}")

    def _populate_recetas_treeview(self, recetas_to_display):
        """Rellena el treeview de recetas existentes con la lista dada."""
        for receta in recetas_to_display:
            try:
                receta_id = receta['id']
                nombre = receta['nombre']
                categoria = receta['categoria']
                precio_venta = receta['precio_venta']
                costo_mano_obra = receta['costo_mano_obra_total']

                # Calcular el costo de ingredientes usando el manager
                costo_ingredientes = self.recetas_manager.calcular_costo_receta(receta_id, self.productos_manager)
                
                ganancia = precio_venta - costo_ingredientes - costo_mano_obra

                self.tree_recetas_existentes.insert("", "end", values=(
                    receta_id,
                    nombre,
                    categoria,
                    f"{costo_ingredientes:.2f}",
                    f"{costo_mano_obra:.2f}",
                    f"{precio_venta:.2f}",
                    f"{ganancia:.2f}"
                ), tags=("editable",)) # Añadir tag para edición directa
            except Exception as e:
                print(f"Error al procesar receta {receta.get('id', 'N/A')} para listado: {str(e)}")
                # messagebox.showwarning("Advertencia", f"No se pudo calcular el costo para la receta '{receta.get('nombre', 'N/A')}': {str(e)}")

    def _filter_recetas_existentes(self, event=None):
        """Filtra las recetas en el Treeview de recetas existentes."""
        search_term = self.entry_search_recetas.get().strip().lower()
        
        for item in self.tree_recetas_existentes.get_children():
            self.tree_recetas_existentes.delete(item)
        
        if not search_term:
            # Si el campo de búsqueda está vacío, mostrar todos los productos
            self._populate_recetas_treeview(self.all_recetas_data)
        else:
            # Filtrar los productos
            filtered_recetas = [
                r for r in self.all_recetas_data 
                if search_term in r['nombre'].lower() or search_term in r['categoria'].lower()
            ]
            self._populate_recetas_treeview(filtered_recetas)

    def editar_receta_existente(self):
        """Carga los datos de una receta existente en el editor para su modificación."""
        selected = self.tree_recetas_existentes.selection()
        if not selected:
            messagebox.showwarning("Selección requerida", "Seleccione una receta de la lista para editar.")
            return
        
        item = self.tree_recetas_existentes.item(selected)
        receta_id = item['values'][0]
        
        try:
            receta_data = self.recetas_manager.obtener_receta(receta_id)
            if not receta_data:
                messagebox.showerror("Error", "No se pudo cargar la receta seleccionada.")
                return

            # Limpiar el formulario actual
            self.limpiar_formulario()

            # Llenar el formulario con los datos de la receta
            self.entry_nombre_receta.delete(0, tk.END)
            self.entry_nombre_receta.insert(0, receta_data['nombre'])
            self.combo_categoria.set(receta_data['categoria'])
            self.entry_precio_venta.delete(0, tk.END)
            self.entry_precio_venta.insert(0, f"{receta_data['precio_venta']:.2f}")
            self.entry_costo_mano_obra.delete(0, tk.END)
            self.entry_costo_mano_obra.insert(0, f"{receta_data['costo_mano_obra_total']:.2f}")

            # Cargar ingredientes de la receta
            ingredientes_db = self.recetas_manager.obtener_ingredientes_de_receta(receta_id)
            self.ingredientes_en_receta = []
            for ing in ingredientes_db:
                ingrediente_id = ing['ingrediente_id']
                nombre_ingrediente = ing['nombre_ingrediente']
                cantidad = ing['cantidad']
                unidad = ing['unidad']
                costo_promedio = self.productos_manager.obtener_costo_promedio(ingrediente_id)
                self.ingredientes_en_receta.append((ingrediente_id, nombre_ingrediente, cantidad, unidad, costo_promedio))
            
            self.actualizar_treeview_receta()
            self.calcular_costo_total_receta()

            # Cargar trabajadores de la receta
            self.cargar_trabajadores_de_receta(receta_id)

            # Cambiar a la pestaña del editor
            self.notebook.select(self.editor_frame)
            messagebox.showinfo("Receta Cargada", f"Receta '{receta_data['nombre']}' cargada para edición.")

            # Guardar el ID de la receta que se está editando
            self.current_editing_receta_id = receta_id

            # Cambiar el botón "Guardar Receta" a "Actualizar Receta"
            self.btn_guardar_actualizar.config(text="🔄 Actualizar Receta", command=self._actualizar_receta)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la receta para edición: {str(e)}")

    def _actualizar_receta(self):
        """Actualiza una receta existente en la base de datos."""
        if not hasattr(self, 'current_editing_receta_id') or self.current_editing_receta_id is None:
            messagebox.showerror("Error", "No hay ninguna receta seleccionada para actualizar.")
            return

        receta_id = self.current_editing_receta_id
        nombre_receta = self.entry_nombre_receta.get().strip()
        categoria = self.combo_categoria.get()
        precio_venta_str = self.entry_precio_venta.get().strip()

        if not nombre_receta:
            messagebox.showerror("Error", "El nombre de la receta no puede estar vacío.")
            return
        if not self.ingredientes_en_receta:
            messagebox.showerror("Error", "La receta debe contener al menos un ingrediente.")
            return
        
        try:
            precio_venta = Decimal(precio_venta_str)
            if precio_venta < Decimal('0'):
                raise ValueError("El precio de venta no puede ser negativo.")

            # Calcular costo total de mano de obra de los trabajadores
            costo_mano_obra_total = Decimal('0.00')
            for _, _, pago in self.trabajadores_temporales:
                costo_mano_obra_total += pago

            # Iniciar la transacción
            self.recetas_manager.db_connection.get_connection().start_transaction()

            # Actualizar la información básica de la receta
            self.recetas_manager.actualizar_precio_receta(receta_id, precio_venta)
            self.recetas_manager.actualizar_costo_mano_obra_receta(receta_id, costo_mano_obra_total)

            # Eliminar todos los ingredientes actuales de la receta y luego re-agregarlos
            # Esto es una forma simple de manejar actualizaciones complejas de ingredientes.
            # Una alternativa más eficiente sería comparar y solo actualizar/insertar/eliminar diferencias.
            
            # Obtener ingredientes actuales en DB
            current_ingredients_in_db = self.recetas_manager.obtener_ingredientes_de_receta(receta_id)
            current_ingredient_ids_in_db = {ing['ingrediente_id'] for ing in current_ingredients_in_db}
            
            # Ingredientes en la GUI
            new_ingredient_ids_in_gui = {ing[0] for ing in self.ingredientes_en_receta}

            # Eliminar ingredientes que ya no están en la GUI
            for ing_id_db in current_ingredient_ids_in_db:
                if ing_id_db not in new_ingredient_ids_in_gui:
                    self.recetas_manager.eliminar_ingrediente_de_receta(receta_id, ing_id_db)

            # Añadir/Actualizar ingredientes de la GUI
            for ing_id, _, cantidad, unidad, _ in self.ingredientes_en_receta:
                self.recetas_manager.agregar_ingrediente_a_receta(receta_id, ing_id, cantidad, unidad) # Este método ya maneja UPDATE/INSERT

            # Guardar trabajadores
            self.guardar_trabajadores_de_receta(receta_id)

            self.recetas_manager.db_connection.commit() # Confirmar la transacción
            messagebox.showinfo("Éxito", f"Receta '{nombre_receta}' actualizada correctamente.")
            self.limpiar_formulario()
            self.load_recetas_existentes() # Recargar la lista de recetas existentes

            # Restablecer el botón a "Guardar Receta"
            self.btn_guardar_actualizar.config(text="💾 Guardar Receta", command=self.guardar_receta)
            self.current_editing_receta_id = None
            
        except InvalidOperation:
            self.recetas_manager.db_connection.rollback()
            messagebox.showerror("Error de Entrada", "Ingrese valores numéricos válidos para Precio de Venta.")
        except ValueError as ve:
            self.recetas_manager.db_connection.rollback()
            messagebox.showerror("Error de Validación", str(ve))
        except Exception as e:
            self.recetas_manager.db_connection.rollback()
            messagebox.showerror("Error", f"No se pudo actualizar la receta: {str(e)}")

    def eliminar_receta_existente(self):
        """Elimina una receta seleccionada de la base de datos."""
        selected = self.tree_recetas_existentes.selection()
        if not selected:
            messagebox.showwarning("Selección requerida", "Seleccione una receta de la lista para eliminar.")
            return
        
        item = self.tree_recetas_existentes.item(selected)
        receta_id = item['values'][0]
        nombre_receta = item['values'][1]

        if not messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar la receta '{nombre_receta}'? Esta acción es irreversible y eliminará también sus ingredientes asociados."):
            return
        
        try:
            # Iniciar la transacción
            self.recetas_manager.db_connection.get_connection().start_transaction()

            # Eliminar ingredientes asociados primero (si no hay CASCADE DELETE en DB)
            # Asumiendo que la DB tiene CASCADE DELETE o que RecetasManager lo maneja.
            # Si no, se necesitaría un método en RecetasManager para eliminar ingredientes por receta_id.
            # Por ahora, confiamos en que la eliminación de la receta principal maneje las dependencias.
            
            # Eliminar la receta principal
            cursor = self.recetas_manager.db_connection.get_connection().cursor()
            cursor.execute("DELETE FROM recetas WHERE id = %s", (receta_id,))
            cursor.close()

            self.recetas_manager.db_connection.commit()
            messagebox.showinfo("Éxito", f"Receta '{nombre_receta}' eliminada correctamente.")
            self.load_recetas_existentes() # Recargar la lista
            
        except Error as e:
            self.recetas_manager.db_connection.rollback()
            messagebox.showerror("Error de Base de Datos", f"No se pudo eliminar la receta: {str(e)}")
        except Exception as e:
            self.recetas_manager.db_connection.rollback()
            messagebox.showerror("Error", f"Ocurrió un error inesperado al eliminar la receta: {str(e)}")

    def exportar_recetas_csv(self):
        """Exporta los datos de las recetas existentes a un archivo CSV."""
        from tkinter import filedialog
        import csv

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Guardar Reporte de Recetas"
        )
        
        if not file_path:
            return # Usuario canceló

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Escribir encabezados
                headers = [self.tree_recetas_existentes.heading(col)['text'] for col in self.tree_recetas_existentes['columns']]
                writer.writerow(headers)
                
                # Escribir datos
                for item_id in self.tree_recetas_existentes.get_children():
                    row_values = self.tree_recetas_existentes.item(item_id)['values']
                    writer.writerow(row_values)
            
            messagebox.showinfo("Éxito", f"Datos de recetas exportados a:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"No se pudo exportar el archivo CSV: {str(e)}")

    def on_double_click_recetas_existentes(self, event):
        """Permite editar directamente en el Treeview de recetas existentes."""
        region = self.tree_recetas_existentes.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tree_recetas_existentes.identify_column(event.x)
        # Columnas editables: 'costo_mano_obra' (#5) y 'precio_venta' (#6)
        if column not in ("#5", "#6"):
            return

        item_id = self.tree_recetas_existentes.focus()
        if not item_id:
            return

        values = list(self.tree_recetas_existentes.item(item_id, "values"))
        receta_id = values[0]
        nombre_receta = values[1]

        # Determinar qué campo se está editando
        if column == "#5": # Costo Mano de Obra
            title = "Editar Costo de Mano de Obra"
            label_text = f"Nuevo Costo M.O. para '{nombre_receta}' ($):"
            current_value_str = values[4].replace('$', '') # Quitar el signo de dólar
            update_method = self.recetas_manager.actualizar_costo_mano_obra_receta
            value_index = 4
        elif column == "#6": # Precio de Venta
            title = "Editar Precio de Venta"
            label_text = f"Nuevo Precio de Venta para '{nombre_receta}' ($):"
            current_value_str = values[5].replace('$', '') # Quitar el signo de dólar
            update_method = self.recetas_manager.actualizar_precio_receta
            value_index = 5
        else:
            return # No debería llegar aquí si la validación de columna es correcta

        # Crear ventana de edición
        edit_window = tk.Toplevel(self)
        edit_window.title(title)
        edit_window.transient(self.master)
        edit_window.geometry("350x150")
        edit_window.resizable(False, False)
        
        # Update the window to ensure it's fully created before calling grab_set
        edit_window.update_idletasks()
        edit_window.grab_set()

        tk.Label(edit_window, text=label_text, font=("Segoe UI", 10)).pack(pady=10)
        
        entry_var = tk.StringVar()
        entry = ttk.Entry(edit_window, textvariable=entry_var, style="Modern.TEntry")
        entry.pack(pady=5)
        entry.focus_set()
        entry_var.set(current_value_str)

        def save_value():
            try:
                new_value = Decimal(entry_var.get().strip())
                if new_value < Decimal('0'):
                    raise ValueError("El valor no puede ser negativo.")

                # Iniciar transacción
                self.recetas_manager.db_connection.get_connection().start_transaction()
                update_method(receta_id, new_value)
                self.recetas_manager.db_connection.commit()

                messagebox.showinfo("Éxito", "Valor actualizado correctamente.")
                edit_window.destroy()
                self.load_recetas_existentes() # Recargar para ver los cambios y recalcular ganancias

            except InvalidOperation:
                self.recetas_manager.db_connection.rollback()
                messagebox.showerror("Error", "Ingrese un valor numérico válido.")
            except ValueError as ve:
                self.recetas_manager.db_connection.rollback()
                messagebox.showerror("Error de Validación", str(ve))
            except Exception as e:
                self.recetas_manager.db_connection.rollback()
                messagebox.showerror("Error", f"No se pudo actualizar: {str(e)}")

        ttk.Button(edit_window, text="Guardar", command=save_value, style="Accent.TButton").pack(pady=10)
        edit_window.bind("<Return>", lambda e: save_value())
        edit_window.bind("<Escape>", lambda e: edit_window.destroy())

        self.master.wait_window(edit_window) # Esperar a que el diálogo se cierre

    def agregar_trabajador(self):
        """Agrega un trabajador a la lista temporal de trabajadores."""
        nombre_trabajador = self.entry_nombre_trabajador.get().strip()
        pago_str = self.entry_pago_trabajador.get().strip()

        if not nombre_trabajador:
            messagebox.showwarning("Advertencia", "Ingrese el nombre del trabajador.")
            return

        try:
            pago = Decimal(pago_str)
            if pago < Decimal('0'):
                raise ValueError("El pago no puede ser negativo.")
                
            # Agregar a la lista temporal
            # Usamos un ID negativo para identificar trabajadores nuevos que aún no están en la BD
            nuevo_id = -(len(self.trabajadores_temporales) + 1)
            self.trabajadores_temporales.append((nuevo_id, nombre_trabajador, pago))
            
            # Actualizar el Treeview
            self.actualizar_treeview_trabajadores()
            
            # Limpiar campos
            self.entry_nombre_trabajador.delete(0, tk.END)
            self.entry_pago_trabajador.delete(0, tk.END)
            self.entry_pago_trabajador.insert(0, "0.00")
            
        except InvalidOperation:
            messagebox.showerror("Error", "Ingrese un valor numérico válido para el pago.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def eliminar_trabajador(self):
        """Elimina un trabajador seleccionado de la lista temporal."""
        seleccion = self.tree_trabajadores.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un trabajador para eliminar.")
            return
            
        item = self.tree_trabajadores.item(seleccion)
        trabajador_id = item['values'][0]
        
        # Eliminar de la lista temporal
        self.trabajadores_temporales = [
            t for t in self.trabajadores_temporales 
            if t[0] != trabajador_id
        ]
        
        # Actualizar el Treeview
        self.actualizar_treeview_trabajadores()

    def actualizar_treeview_trabajadores(self):
        """Actualiza el Treeview de trabajadores con los trabajadores temporales."""
        # Limpiar el Treeview
        for item in self.tree_trabajadores.get_children():
            self.tree_trabajadores.delete(item)
            
        # Agregar trabajadores temporales
        for trabajador_id, nombre, pago in self.trabajadores_temporales:
            self.tree_trabajadores.insert("", "end", values=(
                trabajador_id,
                nombre,
                f"${pago:.2f}"
            ))

    def cargar_trabajadores_de_receta(self, receta_id):
        """Carga los trabajadores de una receta existente."""
        try:
            # Limpiar lista temporal
            self.trabajadores_temporales = []
            
            # Obtener trabajadores de la base de datos
            trabajadores_db = self.recetas_manager.obtener_trabajadores_de_receta(receta_id)
            
            # Agregar a la lista temporal con sus IDs reales
            for trabajador in trabajadores_db:
                self.trabajadores_temporales.append((
                    trabajador['id'],
                    trabajador['nombre_trabajador'],
                    trabajador['pago']
                ))
                
            # Actualizar el Treeview
            self.actualizar_treeview_trabajadores()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los trabajadores: {str(e)}")

    def guardar_trabajadores_de_receta(self, receta_id):
        """Guarda los trabajadores de una receta en la base de datos."""
        try:
            # Guardar trabajadores nuevos (ID negativo)
            for trabajador_id, nombre, pago in self.trabajadores_temporales:
                if trabajador_id < 0:  # Trabajador nuevo
                    self.recetas_manager.agregar_trabajador_a_receta(receta_id, nombre, pago)
                    
            # Para trabajadores existentes, podríamos implementar actualización
            # pero por simplicidad, eliminamos todos y volvemos a agregar
            # En una implementación más completa, se compararía con la BD original
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron guardar los trabajadores: {str(e)}")

