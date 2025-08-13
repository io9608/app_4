import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from Core.UnitConverter import UnitConverter

class GestionCompras(tk.Frame):
    def __init__(self, parent, compras_manager, productos_manager, on_compra_exitosa_callback=None):
        super().__init__(parent)
        self.compras_manager = compras_manager
        self.productos_manager = productos_manager
        self.on_compra_exitosa_callback = on_compra_exitosa_callback
        self.unit_converter = UnitConverter()
        
        self.producto_actual_id = None # Para almacenar el ID del producto seleccionado/creado
        self.producto_actual_unidad_base = None # Para almacenar la unidad base del producto
        self.producto_actual_unidad_display = None # Para almacenar la unidad display del producto

        self._create_widgets()
        self._setup_layout()
        self._bind_events()
        self._load_history()
        self._load_product_names_for_autocomplete() # Cargar nombres para autocompletado

    def _create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        # Frame principal
        self.main_frame = ttk.Frame(self, style="TFrame") # Aplicar estilo
        
        # Título
        self.lbl_title = ttk.Label(
            self.main_frame, 
            text="REGISTRO DE COMPRAS",
            font=('Helvetica', 14, 'bold'),
            style="Titulo.TLabel" # Aplicar estilo
        )
        
        # Formulario de compra
        self.frm_compra = ttk.LabelFrame(
            self.main_frame,
            text="Nueva Compra",
            padding=10,
            style="Card.TFrame" # Aplicar estilo de tarjeta
        )
        
        # --- Campos Comunes a Todos los Tipos de Compra ---
        # Nombre del Producto (Entry para buscar/crear con autocompletado)
        self.lbl_nombre_producto = ttk.Label(self.frm_compra, text="Nombre Producto:")
        self.ent_nombre_producto = ttk.Entry(self.frm_compra, width=30, style="Modern.TEntry") # Aplicar estilo
        self.listbox_autocomplete = tk.Listbox(self.frm_compra, height=5, exportselection=False) # Listbox para autocompletado
        
        # Cantidad y Unidad de Compra (lo que se está comprando)
        self.lbl_cantidad_compra = ttk.Label(self.frm_compra, text="Cantidad Compra:")
        self.ent_cantidad_compra = ttk.Entry(self.frm_compra, width=10, style="Modern.TEntry") # Aplicar estilo
        self.lbl_unidad_compra = ttk.Label(self.frm_compra, text="Unidad Compra:")
        self.cbo_unidad_compra = ttk.Combobox(
            self.frm_compra,
            values=self.unit_converter.get_valid_units(), # Usar get_valid_units
            state="readonly",
            width=8,
            style="Modern.TCombobox" # Aplicar estilo
        )
        
        # Precio de Compra (precio por la unidad de compra)
        self.lbl_precio_compra = ttk.Label(self.frm_compra, text="Precio Compra ($):")
        self.ent_precio_compra = ttk.Entry(self.frm_compra, width=10, style="Modern.TEntry") # Aplicar estilo
        
        # Tipo de Compra (Combobox para seleccionar el frame)
        self.lbl_tipo_compra = ttk.Label(self.frm_compra, text="Tipo Compra:")
        self.cbo_tipo_compra = ttk.Combobox(
            self.frm_compra,
            values=['granel', 'paquete', 'unidad'],
            state="readonly",
            style="Modern.TCombobox" # Aplicar estilo
        )
        self.cbo_tipo_compra.set('granel') # Valor por defecto
        
        # Campos para Proveedor y Notas (comunes)
        self.lbl_proveedor = ttk.Label(self.frm_compra, text="Proveedor:")
        self.ent_proveedor = ttk.Entry(self.frm_compra, width=30, style="Modern.TEntry") # Aplicar estilo
        self.lbl_notas = ttk.Label(self.frm_compra, text="Notas:")
        self.ent_notas = ttk.Entry(self.frm_compra, width=30, style="Modern.TEntry") # Aplicar estilo

        # --- Campos Específicos para Productos Nuevos ---
        self.frm_nuevo_producto = ttk.LabelFrame(self.frm_compra, text="Propiedades de Nuevo Producto", padding=5) # LabelFrame
        self.lbl_unidad_default = ttk.Label(self.frm_nuevo_producto, text="Unidad por Defecto (Stock):")
        self.cbo_unidad_default = ttk.Combobox(
            self.frm_nuevo_producto,
            values=self.unit_converter.get_valid_units(), # Usar get_valid_units
            state="readonly",
            width=10,
            style="Modern.TCombobox" # Aplicar estilo
        )
        self.lbl_stock_minimo = ttk.Label(self.frm_nuevo_producto, text="Stock Mínimo:")
        self.ent_stock_minimo = ttk.Entry(self.frm_nuevo_producto, width=10, style="Modern.TEntry") # Aplicar estilo
        
        # --- Frames Dinámicos por Tipo de Compra ---
        self.frm_granel = ttk.Frame(self.frm_compra)
        # No hay campos adicionales para granel/unidad, solo los comunes

        self.frm_paquete = ttk.Frame(self.frm_compra)
        self.lbl_peso_por_paquete = ttk.Label(self.frm_paquete, text="Peso por Paquete:")
        self.ent_peso_por_paquete = ttk.Entry(self.frm_paquete, width=10, style="Modern.TEntry") # Aplicar estilo
        self.lbl_unidades_por_paquete = ttk.Label(self.frm_paquete, text="Unidades por Paquete:")
        self.ent_unidades_por_paquete = ttk.Entry(self.frm_paquete, width=10, style="Modern.TEntry") # Aplicar estilo

        # Total de la Compra (calculado)
        self.lbl_total_compra = ttk.Label(self.frm_compra, text="Total Compra:")
        self.lbl_total_compra_val = ttk.Label(self.frm_compra, text="$0.00", foreground="green", font=('Helvetica', 12, 'bold'))
        
        # Botón Registrar Compra
        self.btn_registrar = ttk.Button(
            self.frm_compra,
            text="Registrar Compra",
            command=self._registrar_compra,
            style="Accent.TButton" # Aplicar estilo Accent
        )
        
        # Historial de Compras
        self.frm_historial = ttk.LabelFrame(self.main_frame, text="Historial de Compras (Últimos 7 Días)", padding=10, style="Card.TFrame") # LabelFrame
        self.tree_historial = ttk.Treeview(
            self.frm_historial, # Poner en frm_historial
            columns=("fecha", "producto", "cantidad", "unidad", "precio_unitario", "precio_total", "tipo", "proveedor"),
            show="headings",
            style="Modern.Treeview" # Aplicar estilo
        )
        
        # Configurar columnas del historial
        for col in ("fecha", "producto", "cantidad", "unidad", "precio_unitario", "precio_total", "tipo", "proveedor"):
            self.tree_historial.heading(col, text=col.replace('_', ' ').capitalize())
            self.tree_historial.column(col, width=100, anchor='center')
        self.tree_historial.column("producto", width=150, anchor='w')
        self.tree_historial.column("cantidad", width=80, anchor='e')
        self.tree_historial.column("precio_unitario", width=100, anchor='e')
        self.tree_historial.column("precio_total", width=100, anchor='e')

        # Scrollbar para el historial
        self.historial_scrollbar = ttk.Scrollbar(self.frm_historial, orient="vertical", command=self.tree_historial.yview, style="Vertical.TScrollbar")
        self.tree_historial.configure(yscrollcommand=self.historial_scrollbar.set)

    def _setup_layout(self):
        """Configura el layout de la interfaz"""
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.lbl_title.pack(pady=(0, 10))
        self.frm_compra.pack(fill='x', pady=(0, 20))
        
        # Grid de campos comunes
        row_idx = 0
        self.lbl_nombre_producto.grid(row=row_idx, column=0, sticky='e', padx=5, pady=5)
        self.ent_nombre_producto.grid(row=row_idx, column=1, sticky='ew', padx=5, pady=5)
        # No hay botón de buscar/crear, la lógica se maneja en _on_product_name_change y _select_autocomplete
        row_idx += 1
        self.listbox_autocomplete.grid(row=row_idx, column=1, sticky='ew', padx=5, pady=0) # Posicionar listbox
        self.listbox_autocomplete.grid_remove() # Ocultar por defecto
        row_idx += 1 # La listbox ocupa una fila

        self.lbl_cantidad_compra.grid(row=row_idx, column=0, sticky='e', padx=5, pady=5)
        self.ent_cantidad_compra.grid(row=row_idx, column=1, padx=5, pady=5)
        self.lbl_unidad_compra.grid(row=row_idx, column=2, sticky='e', padx=5, pady=5)
        self.cbo_unidad_compra.grid(row=row_idx, column=3, padx=5, pady=5)
        row_idx += 1
        
        self.lbl_precio_compra.grid(row=row_idx, column=0, sticky='e', padx=5, pady=5)
        self.ent_precio_compra.grid(row=row_idx, column=1, padx=5, pady=5)
        self.lbl_tipo_compra.grid(row=row_idx, column=2, sticky='e', padx=5, pady=5)
        self.cbo_tipo_compra.grid(row=row_idx, column=3, padx=5, pady=5)
        row_idx += 1

        self.lbl_proveedor.grid(row=row_idx, column=0, sticky='e', padx=5, pady=5)
        self.ent_proveedor.grid(row=row_idx, column=1, sticky='ew', padx=5, pady=5)
        self.lbl_notas.grid(row=row_idx, column=2, sticky='e', padx=5, pady=5)
        self.ent_notas.grid(row=row_idx, column=3, sticky='ew', padx=5, pady=5)
        row_idx += 1

        # Frame para campos de nuevo producto (inicialmente oculto)
        self.frm_nuevo_producto.grid(row=row_idx, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        self.lbl_unidad_default.grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.cbo_unidad_default.grid(row=0, column=1, padx=5, pady=5)
        self.lbl_stock_minimo.grid(row=0, column=2, sticky='e', padx=5, pady=5)
        self.ent_stock_minimo.grid(row=0, column=3, padx=5, pady=5)
        self.frm_nuevo_producto.grid_remove() # Ocultar por defecto
        row_idx += 1

        # Frames dinámicos para tipos de compra
        self.frm_granel.grid(row=row_idx, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        self.frm_paquete.grid(row=row_idx, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        self.frm_paquete.grid_remove() # Ocultar por defecto

        # Campos específicos de paquete
        self.lbl_peso_por_paquete.grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.ent_peso_por_paquete.grid(row=0, column=1, padx=5, pady=5)
        self.lbl_unidades_por_paquete.grid(row=0, column=2, sticky='e', padx=5, pady=5)
        self.ent_unidades_por_paquete.grid(row=0, column=3, padx=5, pady=5)
        row_idx += 1

        # Total y botón registrar
        self.lbl_total_compra.grid(row=row_idx, column=0, sticky='e', padx=5, pady=5)
        self.lbl_total_compra_val.grid(row=row_idx, column=1, sticky='w', padx=5, pady=5)
        row_idx += 1
        
        self.btn_registrar.grid(row=row_idx, column=0, columnspan=4, pady=10)
        
        # Historial
        self.frm_historial.pack(fill='both', expand=True, pady=(20,0))
        self.tree_historial.pack(side=tk.LEFT, fill='both', expand=True)
        self.historial_scrollbar.pack(side=tk.RIGHT, fill='y')

        # Configurar expansión de columnas en frm_compra
        self.frm_compra.grid_columnconfigure(1, weight=1)
        self.frm_compra.grid_columnconfigure(3, weight=1)

    def _bind_events(self):
        """Enlaza eventos a los widgets"""
        self.cbo_tipo_compra.bind("<<ComboboxSelected>>", self._on_tipo_compra_selected)
        self.ent_cantidad_compra.bind("<KeyRelease>", self._calcular_total_compra)
        self.ent_precio_compra.bind("<KeyRelease>", self._calcular_total_compra)
        self.ent_peso_por_paquete.bind("<KeyRelease>", self._calcular_total_compra)
        self.ent_unidades_por_paquete.bind("<KeyRelease>", self._calcular_total_compra)
        
        # Eventos para autocompletado
        self.ent_nombre_producto.bind("<KeyRelease>", self._on_product_name_change)
        self.listbox_autocomplete.bind("<<ListboxSelect>>", self._select_autocomplete)
        self.ent_nombre_producto.bind("<FocusOut>", self._hide_autocomplete_if_not_selected)
        self.listbox_autocomplete.bind("<FocusOut>", self._hide_autocomplete_if_not_selected)
        self.ent_nombre_producto.bind("<Return>", self._select_first_autocomplete_entry) # Seleccionar primera opción con Enter

    def _load_product_names_for_autocomplete(self):
        """Carga todos los nombres de productos para el autocompletado."""
        try:
            self.all_product_names = self.productos_manager.obtener_nombres_productos()
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los nombres de productos para autocompletado: {str(e)}")
            self.all_product_names = []

    def _on_product_name_change(self, event=None):
        """Maneja el cambio en el campo de nombre de producto para autocompletado."""
        current_text = self.ent_nombre_producto.get().strip().lower()
        
        if not current_text:
            self.listbox_autocomplete.grid_remove()
            self._reset_producto_fields() # Resetear si el campo está vacío
            return

        matches = [name for name in self.all_product_names if current_text in name.lower()]
        
        self.listbox_autocomplete.delete(0, tk.END)
        if matches:
            for match in matches:
                self.listbox_autocomplete.insert(tk.END, match)
            self.listbox_autocomplete.grid() # Mostrar listbox
            self.listbox_autocomplete.lift() # Asegurarse de que esté encima
        else:
            self.listbox_autocomplete.grid_remove()
        
        # Si no hay coincidencias o el texto no es un producto existente, preparar para nuevo producto
        if current_text not in [name.lower() for name in self.all_product_names]:
            self._prepare_for_new_product(self.ent_nombre_producto.get().strip())
        else:
            # Si el texto coincide exactamente con un producto existente, cargar sus datos
            self._load_existing_product_data(self.ent_nombre_producto.get().strip())

    def _select_autocomplete(self, event=None):
        """Selecciona un elemento del autocompletado y lo pone en el Entry."""
        if self.listbox_autocomplete.curselection():
            selected_name = self.listbox_autocomplete.get(self.listbox_autocomplete.curselection())
            self.ent_nombre_producto.delete(0, tk.END)
            self.ent_nombre_producto.insert(0, selected_name)
            self.listbox_autocomplete.grid_remove()
            self._load_existing_product_data(selected_name) # Cargar datos del producto seleccionado
            self.ent_nombre_producto.focus_set() # Devolver el foco al entry

    def _select_first_autocomplete_entry(self, event=None):
        """Selecciona la primera entrada del autocompletado si hay alguna."""
        if self.listbox_autocomplete.size() > 0:
            self.listbox_autocomplete.selection_set(0)
            self._select_autocomplete()
            return "break" # Evitar que el evento Return se propague
        return None

    def _hide_autocomplete_if_not_selected(self, event=None):
        """Oculta el listbox de autocompletado si el foco se pierde y no se seleccionó nada."""
        # Usar un pequeño retraso para permitir que _select_autocomplete se ejecute si se hizo clic
        self.after(100, lambda: self._check_and_hide_autocomplete())

    def _check_and_hide_autocomplete(self):
        if not self.listbox_autocomplete.winfo_exists(): # Si ya fue destruido/ocultado por selección
            return
        # Si el foco no está en el entry ni en el listbox, ocultar
        if self.focus_get() != self.ent_nombre_producto and self.focus_get() != self.listbox_autocomplete:
            self.listbox_autocomplete.grid_remove()
            # Después de ocultar, verificar si el producto es nuevo o existente
            self._check_product_status_on_focus_out()

    def _check_product_status_on_focus_out(self):
        """Verifica el estado del producto cuando el campo de nombre pierde el foco."""
        nombre_producto = self.ent_nombre_producto.get().strip()
        if not nombre_producto:
            self._reset_producto_fields()
            return

        producto_data = self.productos_manager.obtener_producto_por_nombre(nombre_producto)
        if producto_data:
            self._load_existing_product_data(nombre_producto)
        else:
            self._prepare_for_new_product(nombre_producto)

    def _load_existing_product_data(self, nombre_producto: str):
        """Carga los datos de un producto existente en el formulario."""
        producto_data = self.productos_manager.obtener_producto_por_nombre(nombre_producto)
        if producto_data:
            self.producto_actual_id = producto_data[0]
            self.producto_actual_unidad_base = producto_data[3]
            self.producto_actual_unidad_display = producto_data[7]
            stock_minimo_existente = producto_data[6]
            proveedor_existente = producto_data[8]

            # Deshabilitar campos de nuevo producto
            self.frm_nuevo_producto.grid_remove()
            self.cbo_unidad_default.set(self.producto_actual_unidad_display)
            self.ent_stock_minimo.delete(0, tk.END)
            self.ent_stock_minimo.insert(0, str(stock_minimo_existente))
            self.ent_proveedor.delete(0, tk.END)
            self.ent_proveedor.insert(0, str(proveedor_existente) if proveedor_existente else "")

            self.cbo_unidad_default.config(state="disabled")
            self.ent_stock_minimo.config(state="disabled")
            
            # Establecer la unidad de compra por defecto a la unidad display del producto
            self.cbo_unidad_compra.set(self.producto_actual_unidad_display)
            # Filtrar unidades de compra para que solo muestre las compatibles con la unidad base del producto
            self._filter_unidad_compra_options(self.producto_actual_unidad_base)
        else:
            # Si por alguna razón no se encuentra, tratar como nuevo producto
            self._prepare_for_new_product(nombre_producto)

    def _prepare_for_new_product(self, nombre_producto: str):
        """Prepara la interfaz para la creación de un nuevo producto."""
        self.producto_actual_id = None
        self.producto_actual_unidad_base = None
        self.producto_actual_unidad_display = None

        # Habilitar campos de nuevo producto
        self.frm_nuevo_producto.grid()
        self.cbo_unidad_default.config(state="readonly")
        self.ent_stock_minimo.config(state="normal")
        self.cbo_unidad_default.set("") # Limpiar selección
        self.ent_stock_minimo.delete(0, tk.END)
        self.ent_proveedor.delete(0, tk.END) # Limpiar proveedor para nuevo producto
        self.cbo_unidad_compra.set("") # Limpiar unidad de compra
        self._filter_unidad_compra_options(None) # Mostrar todas las unidades

    def _reset_producto_fields(self):
        """Resetea los campos relacionados con la selección/creación de producto."""
        self.producto_actual_id = None
        self.producto_actual_unidad_base = None
        self.producto_actual_unidad_display = None
        
        self.frm_nuevo_producto.grid_remove()
        self.cbo_unidad_default.config(state="readonly")
        self.ent_stock_minimo.config(state="normal")
        self.cbo_unidad_default.set("")
        self.ent_stock_minimo.delete(0, tk.END)
        self.ent_proveedor.delete(0, tk.END)
        self.cbo_unidad_compra.set("") # Limpiar unidad de compra
        self._filter_unidad_compra_options(None) # Mostrar todas las unidades

    def _filter_unidad_compra_options(self, base_unit: str = None):
        """
        Filtra las opciones del combobox de unidad de compra
        para mostrar solo las compatibles con la unidad base del producto.
        Si base_unit es None, muestra todas las unidades válidas.
        """
        if base_unit:
            unit_type = self.unit_converter.UNIT_TYPES.get(base_unit)
            if unit_type:
                compatible_units = self.unit_converter.get_units_by_type(unit_type)
                self.cbo_unidad_compra['values'] = compatible_units
                if self.cbo_unidad_compra.get() not in compatible_units:
                    self.cbo_unidad_compra.set("") # Limpiar si la unidad actual no es compatible
            else:
                # Si la unidad base no tiene un tipo, mostrar todas las unidades
                self.cbo_unidad_compra['values'] = self.unit_converter.get_valid_units()
        else:
            # Si no hay producto seleccionado o es nuevo, mostrar todas las unidades
            self.cbo_unidad_compra['values'] = self.unit_converter.get_valid_units()


    def _on_tipo_compra_selected(self, event=None):
        """Muestra/oculta campos según el tipo de compra seleccionado"""
        tipo_compra = self.cbo_tipo_compra.get()
        
        # Ocultar todos los frames específicos primero
        self.frm_granel.grid_remove()
        self.frm_paquete.grid_remove()

        # Mostrar el frame correspondiente
        if tipo_compra == 'granel' or tipo_compra == 'unidad':
            self.frm_granel.grid()
        elif tipo_compra == 'paquete':
            self.frm_paquete.grid()
        
        self._calcular_total_compra() # Recalcular total al cambiar tipo de compra

    def _calcular_total_compra(self, event=None):
        """Calcula y muestra el total de la compra."""
        try:
            cantidad_compra = Decimal(self.ent_cantidad_compra.get() or '0')
            precio_compra = Decimal(self.ent_precio_compra.get() or '0')
            
            total = cantidad_compra * precio_compra
            self.lbl_total_compra_val.config(text=f"${total:.2f}")
        except InvalidOperation:
            self.lbl_total_compra_val.config(text="$0.00")
        except Exception:
            self.lbl_total_compra_val.config(text="$0.00")

    def _registrar_compra(self):
        """Registra una nueva compra."""
        nombre_producto = self.ent_nombre_producto.get().strip()
        cantidad_str = self.ent_cantidad_compra.get().strip()
        unidad_compra = self.cbo_unidad_compra.get().strip()
        precio_compra_str = self.ent_precio_compra.get().strip()
        tipo_compra = self.cbo_tipo_compra.get().strip()
        proveedor = self.ent_proveedor.get().strip()
        notas = self.ent_notas.get().strip()

        # Campos condicionales
        peso_por_paquete = None
        unidades_por_paquete = None
        stock_minimo = None
        unidad_display = None

        try:
            cantidad = Decimal(cantidad_str)
            precio_unitario = Decimal(precio_compra_str)

            # Validar campos de nuevo producto si aplica
            if self.producto_actual_id is None: # Es un producto nuevo
                stock_minimo_str = self.ent_stock_minimo.get().strip()
                unidad_display = self.cbo_unidad_default.get().strip()
                
                if not stock_minimo_str:
                    raise ValueError("Para un producto nuevo, el stock mínimo es obligatorio.")
                if not unidad_display:
                    raise ValueError("Para un producto nuevo, la unidad por defecto es obligatoria.")
                
                stock_minimo = Decimal(stock_minimo_str)

            # Validar campos específicos del tipo de compra
            if tipo_compra == 'paquete':
                peso_str = self.ent_peso_por_paquete.get().strip()
                unidades_str = self.ent_unidades_por_paquete.get().strip()

                if not peso_str and not unidades_str:
                    raise ValueError("Para compra por paquete, debe especificar 'Peso por Paquete' o 'Unidades por Paquete'.")
                
                if peso_str:
                    peso_por_paquete = Decimal(peso_str)
                if unidades_str:
                    unidades_por_paquete = int(unidades_str)

            # Llamar al manager de compras
            success = self.compras_manager.registrar_compra(
                nombre_producto=nombre_producto,
                cantidad=cantidad,
                unidad=unidad_compra,
                precio_unitario=precio_unitario,
                tipo_compra=tipo_compra,
                proveedor=proveedor,
                notas=notas,
                peso_por_paquete=peso_por_paquete,
                unidades_por_paquete=unidades_por_paquete,
                stock_minimo=stock_minimo, # Solo se usará si el producto es nuevo
                unidad_display=unidad_display # Solo se usará si el producto es nuevo
            )

            if success:
                messagebox.showinfo("Éxito", "Compra registrada correctamente.")
                self._clear_form()
                self._load_history()
                self._load_product_names_for_autocomplete() # Recargar nombres para autocompletado
                if self.on_compra_exitosa_callback:
                    self.on_compra_exitosa_callback() # Recargar productos en la otra página (GestionProductos)
            else:
                messagebox.showerror("Error", "No se pudo registrar la compra.")

        except (InvalidOperation, ValueError) as e:
            messagebox.showerror("Error de Validación", str(e))
        except Exception as e:
            messagebox.showerror("Error al Registrar Compra", f"Ocurrió un error inesperado: {str(e)}")

    def _clear_form(self):
        """Limpia todos los campos del formulario."""
        self.ent_nombre_producto.delete(0, tk.END)
        self.ent_cantidad_compra.delete(0, tk.END)
        self.cbo_unidad_compra.set("")
        self.ent_precio_compra.delete(0, tk.END)
        self.cbo_tipo_compra.set("granel") # Reset a valor por defecto
        self.ent_proveedor.delete(0, tk.END)
        self.ent_notas.delete(0, tk.END)
        self.ent_peso_por_paquete.delete(0, tk.END)
        self.ent_unidades_por_paquete.delete(0, tk.END)
        self.ent_stock_minimo.delete(0, tk.END)
        self.cbo_unidad_default.set("")
        self.lbl_total_compra_val.config(text="$0.00")
        self._reset_producto_fields() # Resetear campos de producto nuevo/existente
        self._on_tipo_compra_selected() # Asegurar que los frames dinámicos se reseteen
        self.listbox_autocomplete.grid_remove() # Ocultar listbox de autocompletado

    def _load_history(self, days=7):
        """Carga el historial de compras."""
        for item in self.tree_historial.get_children():
            self.tree_historial.delete(item)
            
        try:
            compras = self.compras_manager.obtener_historial(days=days)
            for compra in compras:
                # Asegurarse de que los valores Decimal se formateen correctamente
                cantidad_fmt = f"{compra['cantidad']:.4f}"
                precio_unitario_fmt = f"${compra['precio_unitario']:.2f}"
                precio_total_fmt = f"${compra['precio_total']:.2f}"

                self.tree_historial.insert('', 'end', values=(
                    compra['fecha_compra'].strftime('%Y-%m-%d %H:%M'), # Formato de fecha y hora
                    compra['nombre_producto'],
                    cantidad_fmt,
                    compra['unidad'],
                    precio_unitario_fmt,
                    precio_total_fmt,
                    compra['tipo_compra'],
                    compra['proveedor'] if compra['proveedor'] else 'N/A'
                ))
        except Exception as e:
            messagebox.showerror("Error de Historial", f"No se pudo cargar el historial de compras: {str(e)}")
