import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal, InvalidOperation
from Core.UnitConverter import UnitConverter
from Core.productos import Productos # Asegurarse de que Productos esté importado para obtener datos de productos

# --- Clase de Diálogo Personalizado para Cantidad y Unidad (Reutilizada de RecetasEditor) ---
# Esta clase es útil para pedir la cantidad y unidad de un ingrediente a usar.
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
        tk.Label(master, text="Cantidad a usar:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_cantidad = ttk.Entry(master, style="Modern.TEntry")
        self.entry_cantidad.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.entry_cantidad.insert(0, str(self.initial_quantity) if self.initial_quantity is not None else "1.0")
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

        master.grid_columnconfigure(1, weight=1)
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


class GestionProduccion(tk.Frame):
    def __init__(self, parent, produccion_manager, productos_manager):
        super().__init__(parent)
        self.produccion_manager = produccion_manager
        self.productos_manager = productos_manager
        self.unit_converter = UnitConverter()
        # Almacena (ingrediente_id, nombre, cantidad_total_usada, unidad_ingrediente, costo_promedio_ingrediente)
        self.ingredientes_temporales = [] 
        
        self.create_widgets()
        self.load_materias_primas() # Cargar materias primas al inicio
        self.actualizar_treeview_ingredientes_produccion() # Asegurarse de que esté vacío al inicio
        self.calcular_costo_total_produccion() # Calcular costo inicial (0.00)

    def create_widgets(self):
        # Frame principal de la página
        main_frame = ttk.Frame(self, padding=20, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título de la página
        ttk.Label(main_frame, text="REGISTRO DE PRODUCCIÓN", font=("Helvetica", 16, "bold"), style="Titulo.TLabel").grid(row=0, column=0, columnspan=4, pady=(0, 20), sticky="w")

        # --- Sección de Información del Producto Elaborado ---
        info_elaborado_frame = ttk.LabelFrame(main_frame, text="Producto Elaborado", padding=10, style="Card.TFrame")
        info_elaborado_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 10))
        info_elaborado_frame.columnconfigure(1, weight=1) # Permitir expansión del campo de entrada

        ttk.Label(info_elaborado_frame, text="Nombre del Producto:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.entry_nombre_elaborado = ttk.Entry(info_elaborado_frame, width=40, style="Modern.TEntry")
        self.entry_nombre_elaborado.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(info_elaborado_frame, text="Cantidad Producida:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.entry_cantidad_producida = ttk.Entry(info_elaborado_frame, width=15, style="Modern.TEntry")
        self.entry_cantidad_producida.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        self.entry_cantidad_producida.insert(0, "1.0") # Valor por defecto

        ttk.Label(info_elaborado_frame, text="Unidad Producida:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.combobox_unidad_producida = ttk.Combobox(info_elaborado_frame,
            state="readonly",
            values=self.unit_converter.get_valid_units(),
            width=15, style="Modern.TCombobox")
        self.combobox_unidad_producida.grid(row=1, column=3, sticky="w", padx=5, pady=2)

        # --- Contenedor para los Treeviews y Controles ---
        content_frame = ttk.Frame(main_frame, style="TFrame")
        content_frame.grid(row=2, column=0, columnspan=4, sticky="nsew", pady=(10, 0))
        content_frame.grid_columnconfigure(0, weight=1) # Materias Primas
        content_frame.grid_columnconfigure(1, weight=0) # Botones de acción
        content_frame.grid_columnconfigure(2, weight=1) # Ingredientes de Producción
        content_frame.grid_rowconfigure(0, weight=1)

        # --- Panel Izquierdo: Materias Primas Disponibles ---
        mp_frame = ttk.LabelFrame(content_frame, text="Inventario de Materias Primas", padding=10, style="Card.TFrame")
        mp_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        mp_frame.grid_rowconfigure(0, weight=1)
        mp_frame.grid_columnconfigure(0, weight=1)

        self.tree_materias_primas = ttk.Treeview(mp_frame, columns=('id', 'nombre', 'stock', 'unidad'), show='headings', style="Modern.Treeview")
        self.tree_materias_primas.heading('id', text='ID')
        self.tree_materias_primas.heading('nombre', text='Materia Prima')
        self.tree_materias_primas.heading('stock', text='Disponible')
        self.tree_materias_primas.heading('unidad', text='Unidad')
        self.tree_materias_primas.column('id', width=40, anchor='center')
        self.tree_materias_primas.column('nombre', width=150, anchor='w')
        self.tree_materias_primas.column('stock', width=80, anchor='e')
        self.tree_materias_primas.column('unidad', width=60, anchor='center')
        self.tree_materias_primas.grid(row=0, column=0, sticky="nsew")
        
        mp_scrollbar = ttk.Scrollbar(mp_frame, orient="vertical", command=self.tree_materias_primas.yview, style="Vertical.TScrollbar")
        mp_scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree_materias_primas.configure(yscrollcommand=mp_scrollbar.set)

        # --- Panel Central: Botones de Acción ---
        action_buttons_frame = ttk.Frame(content_frame, style="TFrame")
        action_buttons_frame.grid(row=0, column=1, sticky="ns", padx=5, pady=5)

        ttk.Button(action_buttons_frame, text="➡️ Añadir a Producción", command=self.agregar_ingrediente_a_produccion, style="Modern.TButton").pack(pady=5, fill=tk.X)
        ttk.Button(action_buttons_frame, text="⬅️ Eliminar de Producción", command=self.eliminar_ingrediente_de_produccion, style="Modern.TButton").pack(pady=5, fill=tk.X)

        # --- Panel Derecho: Ingredientes para la Producción Actual ---
        ingredientes_produccion_frame = ttk.LabelFrame(content_frame, text="Ingredientes para esta Producción", padding=10, style="Card.TFrame")
        ingredientes_produccion_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        ingredientes_produccion_frame.grid_rowconfigure(0, weight=1)
        ingredientes_produccion_frame.grid_columnconfigure(0, weight=1)

        self.tree_ingredientes_produccion = ttk.Treeview(ingredientes_produccion_frame, 
                                                        columns=('id', 'nombre', 'cantidad_usada', 'costo_parcial'),
                                                        show='headings', style="Modern.Treeview")
        self.tree_ingredientes_produccion.heading('id', text='ID')
        self.tree_ingredientes_produccion.heading('nombre', text='Ingrediente')
        self.tree_ingredientes_produccion.heading('cantidad_usada', text='Cantidad Usada')
        self.tree_ingredientes_produccion.heading('costo_parcial', text='Costo Parcial')
        self.tree_ingredientes_produccion.column('id', width=40, anchor='center')
        self.tree_ingredientes_produccion.column('nombre', width=150, anchor='w')
        self.tree_ingredientes_produccion.column('cantidad_usada', width=100, anchor='e')
        self.tree_ingredientes_produccion.column('costo_parcial', width=80, anchor='e')
        self.tree_ingredientes_produccion.grid(row=0, column=0, sticky="nsew")

        ing_prod_scrollbar = ttk.Scrollbar(ingredientes_produccion_frame, orient="vertical", command=self.tree_ingredientes_produccion.yview, style="Vertical.TScrollbar")
        ing_prod_scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree_ingredientes_produccion.configure(yscrollcommand=ing_prod_scrollbar.set)

        # --- Resumen de Costo y Botones de Control ---
        summary_controls_frame = ttk.Frame(main_frame, style="TFrame")
        summary_controls_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        summary_controls_frame.columnconfigure(1, weight=1) # Para que el valor del costo se expanda

        ttk.Label(summary_controls_frame, text="Costo Total de Ingredientes:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.costo_total_var = tk.StringVar(value="$0.00")
        ttk.Label(summary_controls_frame, textvariable=self.costo_total_var, font=('Helvetica', 12, 'bold'), foreground="blue").grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Button(summary_controls_frame, text="💾 Registrar Producción", command=self.registrar_produccion, style="Accent.TButton").grid(row=1, column=0, columnspan=2, pady=(10, 5), sticky="ew")
        ttk.Button(summary_controls_frame, text="🧹 Limpiar Formulario", command=self.limpiar_formulario, style="Modern.TButton").grid(row=2, column=0, columnspan=2, pady=(5, 0), sticky="ew")

        # Configurar expansión de filas y columnas en el main_frame
        main_frame.grid_rowconfigure(2, weight=1) # El content_frame (que contiene los treeviews)
        main_frame.grid_columnconfigure(0, weight=1) # Permitir que la primera columna se expanda

        # Eventos
        self.tree_materias_primas.bind('<Double-1>', self.agregar_ingrediente_a_produccion)
        self.tree_ingredientes_produccion.bind('<Delete>', self.eliminar_ingrediente_de_produccion) # Permite eliminar con tecla Supr
        self.tree_ingredientes_produccion.bind('<Double-1>', self.editar_cantidad_ingrediente_produccion) # Editar cantidad de ingrediente

    def load_materias_primas(self):
        """Carga las materias primas disponibles en el Treeview de inventario."""
        for item in self.tree_materias_primas.get_children():
            self.tree_materias_primas.delete(item)
        
        try:
            productos = self.productos_manager.obtener_todos_los_productos()
            for p in productos:
                # p: (id, nombre_producto, cantidad, unidad, total_invertido, notas, stock_minimo, unidad_display, proveedor)
                prod_id, nombre, cantidad, unidad_interna, total_invertido, _, _, unidad_display, _ = p
                
                costo_promedio = self.productos_manager.obtener_costo_promedio(prod_id)

                self.tree_materias_primas.insert('', 'end', 
                                            values=(prod_id, nombre, f"{float(cantidad):.4f} {unidad_display}", unidad_display),
                                            tags=(str(prod_id), str(costo_promedio), unidad_interna)) # Guardamos ID, costo_promedio y unidad_interna en tags
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar las materias primas: {str(e)}")

    def agregar_ingrediente_a_produccion(self, event=None):
        """Agrega el ingrediente seleccionado del inventario a la lista de producción."""
        seleccion = self.tree_materias_primas.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Seleccione una materia prima del inventario para añadir a la producción.")
            return
        
        item = self.tree_materias_primas.item(seleccion)
        ingrediente_id = item['values'][0]
        nombre_ingrediente = item['values'][1]
        unidad_display_producto = item['values'][3] # Unidad de display del producto
        costo_promedio_ingrediente = Decimal(item['tags'][1]) # Costo promedio guardado en tags
        unidad_interna_base_ingrediente = item['tags'][2] # Unidad interna base del producto

        unit_type = self.unit_converter.UNIT_TYPES.get(unidad_interna_base_ingrediente) # Usar unidad_interna_base para el tipo
        if not unit_type:
            messagebox.showerror("Error de Unidad", f"La unidad base interna '{unidad_interna_base_ingrediente}' del producto '{nombre_ingrediente}' no tiene un tipo de magnitud definido en UnitConverter. No se puede añadir.")
            return

        # Verificar si el ingrediente ya está en la lista temporal para obtener la cantidad actual
        current_quantity = None
        current_unit = None
        for i, (existing_id, _, existing_quantity, existing_unit, _) in enumerate(self.ingredientes_temporales):
            if existing_id == ingrediente_id:
                current_quantity = existing_quantity
                current_unit = existing_unit
                break

        dialog = CantidadUnidadDialog(self, 
                                      f"Cantidad de {nombre_ingrediente} a usar", 
                                      current_unit if current_unit else unidad_display_producto, # Unidad por defecto
                                      unit_type, 
                                      self.unit_converter,
                                      initial_quantity=current_quantity)
        
        cantidad = dialog.result_cantidad
        unidad_elegida = dialog.result_unidad

        if cantidad is None or unidad_elegida is None: # Usuario canceló o validación falló en el diálogo
            return
        
        # Actualizar o añadir a la lista temporal de ingredientes de producción
        if current_quantity is not None:
            # Actualizar cantidad y unidad si ya existe
            for i, (existing_id, _, _, _, _) in enumerate(self.ingredientes_temporales):
                if existing_id == ingrediente_id:
                    self.ingredientes_temporales[i] = (ingrediente_id, nombre_ingrediente, cantidad, unidad_elegida, costo_promedio_ingrediente)
                    break
        else:
            # Añadir nuevo ingrediente
            self.ingredientes_temporales.append((ingrediente_id, nombre_ingrediente, cantidad, unidad_elegida, costo_promedio_ingrediente))
        
        self.actualizar_treeview_ingredientes_produccion()
        self.calcular_costo_total_produccion()
        messagebox.showinfo("Ingrediente Agregado/Actualizado", f"'{nombre_ingrediente}' añadido/actualizado a la producción a {cantidad:.4f} {unidad_elegida}.")
    
    def editar_cantidad_ingrediente_produccion(self, event=None):
        """Permite editar la cantidad de un ingrediente ya en la lista de producción."""
        seleccion = self.tree_ingredientes_produccion.selection()
        if not seleccion:
            return # No hay nada seleccionado
        
        item = self.tree_ingredientes_produccion.item(seleccion)
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
        for i, (ing_id, nombre, _, _, costo_promedio) in enumerate(self.ingredientes_temporales):
            if ing_id == ingrediente_id:
                self.ingredientes_temporales[i] = (ing_id, nombre, cantidad_nueva, unidad_nueva, costo_promedio)
                break
        
        self.actualizar_treeview_ingredientes_produccion()
        self.calcular_costo_total_produccion()
        messagebox.showinfo("Actualizado", f"Cantidad de '{nombre_ingrediente}' actualizada a {cantidad_nueva:.4f} {unidad_nueva}.")

    def eliminar_ingrediente_de_produccion(self, event=None):
        """Elimina un ingrediente seleccionado de la lista de producción."""
        seleccion = self.tree_ingredientes_produccion.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Seleccione un ingrediente de la lista de producción para eliminar.")
            return
        
        item = self.tree_ingredientes_produccion.item(seleccion)
        ingrediente_id_a_eliminar = item['values'][0] 
        nombre_ingrediente = item['values'][1]

        if not messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar '{nombre_ingrediente}' de la producción?"):
            return

        self.ingredientes_temporales = [
            ing for ing in self.ingredientes_temporales 
            if ing[0] != ingrediente_id_a_eliminar
        ]
        self.actualizar_treeview_ingredientes_produccion()
        self.calcular_costo_total_produccion()
        messagebox.showinfo("Eliminado", f"Ingrediente '{nombre_ingrediente}' eliminado de la producción.")

    def actualizar_treeview_ingredientes_produccion(self):
        """Actualiza el Treeview de ingredientes de producción con los ingredientes temporales."""
        for item in self.tree_ingredientes_produccion.get_children():
            self.tree_ingredientes_produccion.delete(item)
        
        for ing_id, nombre, cantidad_usada, unidad_usada, costo_promedio_ingrediente in self.ingredientes_temporales:
            producto_data = self.productos_manager.obtener_producto(ing_id)
            costo_parcial = Decimal('0.00')
            if producto_data:
                unidad_base_ingrediente = producto_data[3] # 'unidad' en la tabla productos
                try:
                    cantidad_en_base = self.unit_converter.convert(
                        cantidad_usada, unidad_usada, unidad_base_ingrediente
                    )
                    costo_parcial = cantidad_en_base * costo_promedio_ingrediente
                except Exception as e:
                    print(f"Error al calcular costo parcial para {nombre}: {e}")
            else:
                print(f"Advertencia: Producto ID {ing_id} no encontrado para calcular costo parcial en GUI.")

            self.tree_ingredientes_produccion.insert('', 'end', values=(ing_id, nombre, f"{cantidad_usada:.4f} {unidad_usada}", f"${costo_parcial:.2f}"))

    def calcular_costo_total_produccion(self):
        """Calcula y actualiza el costo total mostrado de la producción."""
        total = Decimal('0.00')
        for ing_id, _, cantidad_usada, unidad_usada, costo_promedio_ingrediente in self.ingredientes_temporales:
            producto_data = self.productos_manager.obtener_producto(ing_id)
            if producto_data:
                unidad_base_ingrediente = producto_data[3]
                try:
                    cantidad_en_base = self.unit_converter.convert(
                        cantidad_usada, unidad_usada, unidad_base_ingrediente
                    )
                    total += cantidad_en_base * costo_promedio_ingrediente
                except Exception as e:
                    print(f"Error al calcular costo total para ingrediente {ing_id}: {e}")
            else:
                print(f"Advertencia: Producto ID {ing_id} no encontrado para calcular costo total.")

        self.costo_total_var.set(f"${total:.2f}")

    def registrar_produccion(self):
        """Registra la producción del producto elaborado."""
        nombre_elaborado = self.entry_nombre_elaborado.get().strip()
        cantidad_producida_str = self.entry_cantidad_producida.get().strip()
        unidad_producida = self.combobox_unidad_producida.get().strip()
        

        if not nombre_elaborado:
            messagebox.showerror("Error", "El nombre del producto elaborado no puede estar vacío.")
            return
        if not cantidad_producida_str:
            messagebox.showerror("Error", "La cantidad producida no puede estar vacía.")
            return
        if not unidad_producida:
            messagebox.showerror("Error", "Debe seleccionar una unidad para el producto producido.")
            return
        if not self.ingredientes_temporales:
            messagebox.showerror("Error", "Debe añadir al menos un ingrediente para registrar la producción.")
            return
        
        try:
            cantidad_producida = Decimal(cantidad_producida_str)
            if cantidad_producida <= Decimal('0'):
                raise ValueError("La cantidad producida debe ser un número positivo.")

            # Preparar la lista de ingredientes para el manager de producción
            # El manager espera (ingrediente_id, cantidad_TOTAL_usada, unidad_ingrediente)
            ingredientes_para_manager = []
            for ing_id, _, cantidad_usada, unidad_usada, _ in self.ingredientes_temporales:
                ingredientes_para_manager.append((ing_id, cantidad_usada, unidad_usada))

            # Llamar al manager de producción con la unidad especificada
            producto_elaborado_id = self.produccion_manager.registrar_produccion(
                nombre_producto_elaborado=nombre_elaborado,
                ingredientes=ingredientes_para_manager,
                cantidad_producida=cantidad_producida,
                unidad_producida=unidad_producida
            )

            messagebox.showinfo("Éxito", f"Producción de '{nombre_elaborado}' registrada correctamente. ID del producto: {producto_elaborado_id}")
            self.limpiar_formulario()
            self.load_materias_primas() # Recargar materias primas para reflejar el stock consumido
            
        except InvalidOperation:
            messagebox.showerror("Error de Entrada", "Ingrese un valor numérico válido para la cantidad producida.")
        except ValueError as ve:
            messagebox.showerror("Error de Validación", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar la producción: {str(e)}")

    def limpiar_formulario(self):
        """Limpia todos los campos del formulario de producción."""
        self.entry_nombre_elaborado.delete(0, tk.END)
        self.entry_cantidad_producida.delete(0, tk.END)
        self.entry_cantidad_producida.insert(0, "1.0")
        self.ingredientes_temporales = []
        self.actualizar_treeview_ingredientes_produccion()
        self.calcular_costo_total_produccion()
        self.load_materias_primas() # Recargar materias primas por si acaso

