import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal
from Core.UnitConverter import UnitConverter
from Core.productos import Productos
from Core.recetas import RecetasManager

class GestionVentas(tk.Frame):
    def __init__(self, parent, ventas_manager, productos_manager, recetas_manager):
        super().__init__(parent)
        self.ventas_manager = ventas_manager
        self.productos_manager = productos_manager
        self.recetas_manager = recetas_manager
        self.unit_converter = UnitConverter()
        
        self.ventas_activas = {}  
        self.current_client_id = None
        
        self.create_widgets()
        self.load_recetas_disponibles()  # Cambiado a solo cargar recetas

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="GESTIÓN DE VENTAS", font=("Helvetica", 16, "bold")).grid(
            row=0, column=0, columnspan=3, pady=10, sticky="w")

        # Panel de control de clientes
        client_control_frame = ttk.LabelFrame(main_frame, text="Clientes", padding=10)
        client_control_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        ttk.Button(client_control_frame, text="Nuevo Cliente", command=self.nuevo_cliente,
                  style="Accent.TButton").pack(fill=tk.X, pady=5)
        ttk.Button(client_control_frame, text="Eliminar Cliente", command=self.eliminar_cliente,
                  style="Modern.TButton").pack(fill=tk.X, pady=5)

        self.client_listbox = tk.Listbox(client_control_frame, height=10, 
                                       selectmode=tk.SINGLE, font=('Helvetica', 10))
        self.client_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.client_listbox.bind('<<ListboxSelect>>', self.seleccionar_cliente)

        # Notebook para pestañas de clientes
        self.client_notebook = ttk.Notebook(main_frame)
        self.client_notebook.grid(row=1, column=1, columnspan=2, sticky="nsew", padx=5, pady=5)

        # Panel de recetas disponibles (antes era productos)
        recetas_frame = ttk.LabelFrame(main_frame, text="Recetas Disponibles", padding=10)
        recetas_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        # Treeview solo para recetas
        self.tree_recetas = ttk.Treeview(recetas_frame, 
                                       columns=('id', 'nombre', 'precio'),
                                       show='headings', height=10)
        
        # Configurar columnas
        columns = [
            ('id', 'ID', 50, 'center'),
            ('nombre', 'Receta', 180, 'w'),
            ('precio', 'Precio Venta', 100, 'e')
        ]
        
        for col_id, text, width, anchor in columns:
            self.tree_recetas.heading(col_id, text=text)
            self.tree_recetas.column(col_id, width=width, anchor=anchor)
            
        self.tree_recetas.pack(fill=tk.BOTH, expand=True)
        self.tree_recetas.bind('<Double-1>', self.agregar_receta_a_venta)

        # Configurar pesos de grid
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

    def load_recetas_disponibles(self):
        """Carga solo las recetas con precio de venta definido"""
        for item in self.tree_recetas.get_children():
            self.tree_recetas.delete(item)
        
        try:
            recetas = self.recetas_manager.obtener_todas_las_recetas()
            
            # Filtrar recetas con precio de venta > 0
            for r in recetas:
                # ACCIÓN: Acceder a los valores del diccionario por clave
                precio_venta = r.get('precio_venta', Decimal('0.00')) # Usar .get para seguridad y valor por defecto
                
                if precio_venta is not None and precio_venta > Decimal('0'):  # Comparar con Decimal('0')
                    self.tree_recetas.insert('', 'end', 
                                          values=(r['id'], r['nombre'], f"${precio_venta:.2f}"),
                                          tags=('receta', str(r['id'])))
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las recetas: {str(e)}")

    def nuevo_cliente(self):
        dialog = NuevoClienteDialog(self, "Información del Cliente")
        if dialog.result_data:
            client_id = f"cliente_{len(self.ventas_activas) + 1}"
            self.ventas_activas[client_id] = {
                'info': dialog.result_data,
                'productos': []  # (id, nombre, precio_unitario, cantidad)
            }
            self.actualizar_lista_clientes()
            self.crear_pestana_cliente(client_id)
            self.client_notebook.select(len(self.client_notebook.tabs())-1)
            self.current_client_id = client_id

    def crear_pestana_cliente(self, client_id):
        tab = ttk.Frame(self.client_notebook)
        self.client_notebook.add(tab, text=self.ventas_activas[client_id]['info']['nombre'])
        
        # Información del cliente
        info_cliente = self.ventas_activas[client_id]['info']
        print(info_cliente)
        info_frame = ttk.LabelFrame(tab, text="Información del Cliente", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Mapa de campos para coincidir con las claves del diccionario
        campo_map = {
            "Nombre:": "nombre",
            "Teléfono:": "telefono",
            "Dirección:": "direccion",
            "Notas:": "notas"
        }
        
        campos = ["Nombre:", "Teléfono:", "Dirección:", "Notas:"]
        for i, campo in enumerate(campos):
            ttk.Label(info_frame, text=campo).grid(row=i, column=0, sticky="w")
            valor = info_cliente.get(campo_map[campo], "No disponible")
            ttk.Label(info_frame, text=valor).grid(row=i, column=1, sticky="w")

        # Productos en la venta
        productos_frame = ttk.LabelFrame(tab, text="Recetas en Venta", padding=10)
        productos_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tree = ttk.Treeview(productos_frame, 
                          columns=('id', 'nombre', 'precio', 'cantidad', 'subtotal'),
                          show='headings')
        
        # Configurar columnas del treeview de venta
        columns = [
            ('id', 'ID', 50, 'center'),
            ('nombre', 'Receta', 200, 'w'),
            ('precio', 'Precio Unitario', 100, 'e'),
            ('cantidad', 'Cantidad', 80, 'e'),
            ('subtotal', 'Subtotal', 100, 'e')
        ]
        
        for col_id, text, width, anchor in columns:
            tree.heading(col_id, text=text)
            tree.column(col_id, width=width, anchor=anchor)
            
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar y eventos
        scrollbar = ttk.Scrollbar(productos_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.bind('<Delete>', lambda e: self.eliminar_producto_venta(tree))
        
        # Guardar referencia al treeview
        self.ventas_activas[client_id]['tree'] = tree
        
        # Total y botones
        total_frame = ttk.Frame(tab)
        total_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.ventas_activas[client_id]['total_var'] = tk.StringVar(value="Total: $0.00")
        ttk.Label(total_frame, textvariable=self.ventas_activas[client_id]['total_var'], 
                 font=('Helvetica', 12, 'bold')).pack(side="left", padx=5)
        
        ttk.Button(total_frame, text="Registrar Venta", 
                  command=lambda: self.registrar_venta(client_id),
                  style="Accent.TButton").pack(side="right", padx=5)
        
        self.actualizar_productos_cliente(client_id)

    def actualizar_productos_cliente(self, client_id):
        """Actualiza el treeview de productos para un cliente"""
        # Verificar que el treeview exista antes de intentar actualizarlo
        if 'tree' not in self.ventas_activas[client_id]:
            return
            
        tree = self.ventas_activas[client_id]['tree']
        for item in tree.get_children():
            tree.delete(item)
        
        total = Decimal('0.00')
        for prod in self.ventas_activas[client_id]['productos']:
            prod_id, nombre, precio_unitario, cantidad = prod
            subtotal = precio_unitario * Decimal(str(cantidad))
            total += subtotal
            tree.insert('', 'end', 
                       values=(prod_id, nombre, f"${precio_unitario:.2f}", 
                               cantidad, f"${subtotal:.2f}"))
        
        self.ventas_activas[client_id]['total_var'].set(f"Total: ${total:.2f}")

    def seleccionar_cliente(self, event):
        """Cuando se selecciona un cliente de la lista"""
        selection = self.client_listbox.curselection()
        if selection:
            client_id = self.client_listbox.get(selection[0]).split(" - ")[0]
            self.current_client_id = client_id
            # Enfocar la pestaña correspondiente
            for i, tab in enumerate(self.client_notebook.tabs()):
                if self.client_notebook.tab(tab, "text") == self.ventas_activas[client_id]['info']['nombre']:
                    self.client_notebook.select(i)
                    break

    def agregar_receta_a_venta(self, event):
        """Agrega una receta a la venta del cliente actual"""
        if not self.current_client_id:
            messagebox.showwarning("Cliente requerido", "Seleccione o cree un cliente primero.")
            return
        
        selection = self.tree_recetas.selection()
        if not selection:
            return
        
        item = self.tree_recetas.item(selection[0])
        receta_id = item['values'][0]
        nombre = item['values'][1]
        precio = Decimal(item['values'][2][1:])  # Remueve el $ y convierte a Decimal
        
        cantidad = simpledialog.askfloat(
            "Cantidad",
            f"Ingrese la cantidad de '{nombre}' a vender:",
            parent=self,
            minvalue=0.1  # Mínimo 0.1 para permitir decimales
        )
        
        if cantidad and cantidad > 0:
            # Verificar si la receta ya está en la venta
            for i, prod in enumerate(self.ventas_activas[self.current_client_id]['productos']):
                if prod[0] == receta_id:
                    # Actualizar cantidad si ya existe
                    self.ventas_activas[self.current_client_id]['productos'][i] = (
                        receta_id, nombre, precio, prod[3] + cantidad
                    )
                    break
            else:
                # Agregar nueva receta a la venta
                self.ventas_activas[self.current_client_id]['productos'].append(
                    (receta_id, nombre, precio, cantidad)
                )
            
            self.actualizar_productos_cliente(self.current_client_id)

    def eliminar_producto_venta(self, tree):
        """Elimina un producto de la venta actual"""
        if not self.current_client_id:
            return
        
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        prod_id = item['values'][0]
        
        # Eliminar de la lista de productos
        self.ventas_activas[self.current_client_id]['productos'] = [
            p for p in self.ventas_activas[self.current_client_id]['productos']
            if p[0] != prod_id
        ]
        
        self.actualizar_productos_cliente(self.current_client_id)

    def eliminar_cliente(self):
        """Elimina el cliente y su pestaña"""
        if not self.current_client_id:
            return
        
        if messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar venta para {self.ventas_activas[self.current_client_id]['info']['nombre']}?"
        ):
            # Eliminar pestaña
            for i, tab in enumerate(self.client_notebook.tabs()):
                if self.client_notebook.tab(tab, "text") == self.ventas_activas[self.current_client_id]['info']['nombre']:
                    self.client_notebook.forget(i)
                    break
            
            # Eliminar de ventas activas
            del self.ventas_activas[self.current_client_id]
            self.current_client_id = None
            self.actualizar_lista_clientes()

    def registrar_venta(self, client_id):
        """Registra la venta en la base de datos"""
        if not self.ventas_activas[client_id]['productos']:
            messagebox.showwarning("Venta vacía", "No hay productos para registrar la venta.")
            return
        
        try:
            # Preparar datos para el manager
            cliente_info = self.ventas_activas[client_id]['info']
            
            # Iterar sobre cada producto en la venta y registrarlo individualmente
            # Esto asume que el manager de ventas registra una receta a la vez.
            for prod in self.ventas_activas[client_id]['productos']:
                receta_id, _, precio_unitario, cantidad = prod
                
                # Llamar al manager de ventas para cada ítem
                # NOTA: El método registrar_venta en Core/ventas.py solo toma cliente_nombre y cliente_notas.
                # Si necesitas registrar más detalles del cliente o un ID de cliente,
                # deberás modificar Core/ventas.py y la tabla 'ventas'.
                self.ventas_manager.registrar_venta(
                    receta_vendida_id=receta_id,
                    cantidad_vendida=int(cantidad), # Asegurarse de que sea int si la DB lo espera así
                    precio_venta=precio_unitario,
                    cliente_nombre=cliente_info['nombre'],
                    cliente_notas=cliente_info['notas']
                )
            
            messagebox.showinfo(
                "Venta Registrada",
                f"Venta(s) registrada(s) correctamente para {cliente_info['nombre']}"
            )
            
            # Limpiar después de registrar
            self.ventas_activas[client_id]['productos'] = []
            self.actualizar_productos_cliente(client_id)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar la venta: {str(e)}")

    def actualizar_lista_clientes(self):
        """Actualiza la lista de clientes activos"""
        self.client_listbox.delete(0, tk.END)
        for client_id, data in self.ventas_activas.items():
            self.client_listbox.insert(
                tk.END, 
                f"{client_id} - {data['info']['nombre']} ({len(data['productos'])} productos)"
            )


class NuevoClienteDialog(simpledialog.Dialog):
    """Diálogo para ingresar información de un nuevo cliente"""
    
    def __init__(self, parent, title):
        self.result_data = None
        super().__init__(parent, title)
    
    def body(self, master):
        ttk.Label(master, text="Nombre:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_nombre = ttk.Entry(master)
        self.entry_nombre.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        
        ttk.Label(master, text="Teléfono:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_telefono = ttk.Entry(master)
        self.entry_telefono.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        
        ttk.Label(master, text="Dirección:").grid(row=2, column=0, sticky="w", pady=5)
        self.entry_direccion = ttk.Entry(master)
        self.entry_direccion.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        
        ttk.Label(master, text="Notas:").grid(row=3, column=0, sticky="nw", pady=5)
        self.text_notas = tk.Text(master, height=4, width=30)
        self.text_notas.grid(row=3, column=1, sticky="ew", pady=5, padx=5)
        
        master.grid_columnconfigure(1, weight=1)
        return self.entry_nombre
    
    def buttonbox(self):
        box = ttk.Frame(self)
        
        ttk.Button(box, text="Aceptar", command=self.ok, style="Accent.TButton").pack(side="left", padx=5, pady=5)
        ttk.Button(box, text="Cancelar", command=self.cancel, style="Modern.TButton").pack(side="left", padx=5, pady=5)
        
        self.bind("<Return>", lambda event: self.ok())
        self.bind("<Escape>", lambda event: self.cancel())
        
        box.pack()
    
    def apply(self):
        nombre = self.entry_nombre.get().strip()
        telefono = self.entry_telefono.get().strip()
        direccion = self.entry_direccion.get().strip()
        notas = self.text_notas.get("1.0", tk.END).strip()
        
        if not nombre:
            messagebox.showerror("Error", "El nombre del cliente es requerido.")
            return
        
        self.result_data = {
            'nombre': nombre,
            'telefono': telefono,
            'direccion': direccion,
            'notas': notas
        }
