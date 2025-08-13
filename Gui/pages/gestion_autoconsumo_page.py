import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from Core.autoconsumo import Autoconsumo
from Core.productos import Productos

class GestionAutoconsumo(tk.Frame):
    def __init__(self, parent, autoconsumo_manager, productos_manager):
        super().__init__(parent)
        self.autoconsumo_manager = autoconsumo_manager
        self.productos_manager = productos_manager
        
        self.create_widgets()
        self.load_productos()
        self.load_historial_autoconsumo()

    def create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        # Frame principal con padding
        main_frame = tk.Frame(self, background="#F5F5F5")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(
            main_frame, 
            text="Gestión de Autoconsumo", 
            font=("Segoe UI", 16, "bold"),
            background="#F5F5F5",
            foreground="#1E88E5"
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20), sticky="w")
        
        # Frame para registrar autoconsumo
        registro_frame = ttk.LabelFrame(main_frame, text="Registrar Autoconsumo", padding=15, style="Card.TFrame")
        registro_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 20))
        registro_frame.columnconfigure(1, weight=1)
        
        # Selección de producto
        ttk.Label(registro_frame, text="Producto:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.combo_producto = ttk.Combobox(registro_frame, state="readonly", style="Modern.TCombobox")
        self.combo_producto.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Cantidad
        ttk.Label(registro_frame, text="Cantidad:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_cantidad = ttk.Entry(registro_frame, style="Modern.TEntry")
        self.entry_cantidad.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.entry_cantidad.config(width=15)
        
        # Unidad (se actualizará según el producto seleccionado)
        ttk.Label(registro_frame, text="Unidad:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.label_unidad = ttk.Label(registro_frame, text="", style="Modern.TLabel")
        self.label_unidad.grid(row=1, column=3, sticky="w", padx=5, pady=5)
        
        # Motivo
        ttk.Label(registro_frame, text="Motivo:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.entry_motivo = ttk.Entry(registro_frame, style="Modern.TEntry")
        self.entry_motivo.grid(row=2, column=1, columnspan=3, sticky="ew", padx=5, pady=5)
        
        # Botón para registrar
        ttk.Button(registro_frame, text="Registrar Autoconsumo", command=self.registrar_autoconsumo, style="Accent.TButton").grid(
            row=3, column=0, columnspan=4, pady=(15, 0)
        )
        
        # Frame para historial
        historial_frame = ttk.LabelFrame(main_frame, text="Historial de Autoconsumo", padding=15, style="Card.TFrame")
        historial_frame.grid(row=2, column=0, columnspan=4, sticky="nsew", pady=(0, 20))
        historial_frame.columnconfigure(0, weight=1)
        historial_frame.rowconfigure(1, weight=1)
        
        # Treeview para historial
        self.tree_historial = ttk.Treeview(historial_frame, columns=(
            "id", "producto", "cantidad", "unidad", "motivo", "fecha", "costo"
        ), show='headings', style="Modern.Treeview", height=10)
        
        self.tree_historial.heading("id", text="ID")
        self.tree_historial.heading("producto", text="Producto")
        self.tree_historial.heading("cantidad", text="Cantidad")
        self.tree_historial.heading("unidad", text="Unidad")
        self.tree_historial.heading("motivo", text="Motivo")
        self.tree_historial.heading("fecha", text="Fecha")
        self.tree_historial.heading("costo", text="Costo ($)")
        
        self.tree_historial.column("id", width=50, anchor="center")
        self.tree_historial.column("producto", width=150)
        self.tree_historial.column("cantidad", width=80, anchor="e")
        self.tree_historial.column("unidad", width=80, anchor="center")
        self.tree_historial.column("motivo", width=200)
        self.tree_historial.column("fecha", width=120, anchor="center")
        self.tree_historial.column("costo", width=100, anchor="e")
        
        self.tree_historial.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        
        # Scrollbar para el historial
        historial_scrollbar = ttk.Scrollbar(historial_frame, orient="vertical", command=self.tree_historial.yview, style="Vertical.TScrollbar")
        historial_scrollbar.grid(row=1, column=1, sticky="ns", pady=(10, 0))
        self.tree_historial.configure(yscrollcommand=historial_scrollbar.set)
        
        # Botón para actualizar historial
        ttk.Button(historial_frame, text="Actualizar Historial", command=self.load_historial_autoconsumo, style="Modern.TButton").grid(
            row=2, column=0, columnspan=2, pady=(10, 0)
        )
        
        # Configurar expansión
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Eventos
        self.combo_producto.bind("<<ComboboxSelected>>", self.on_producto_selected)

    def load_productos(self):
        """Carga los productos en el combobox"""
        try:
            productos = self.productos_manager.obtener_todos_los_productos()
            producto_names = [f"{p[0]} - {p[1]}" for p in productos]  # ID - Nombre
            self.combo_producto['values'] = producto_names
            
            if producto_names:
                self.combo_producto.set(producto_names[0])
                self.on_producto_selected()
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los productos: {str(e)}")

    def on_producto_selected(self, event=None):
        """Actualiza la unidad cuando se selecciona un producto"""
        selected = self.combo_producto.get()
        if selected:
            try:
                producto_id = int(selected.split(" - ")[0])
                producto = self.productos_manager.obtener_producto(producto_id)
                if producto:
                    self.label_unidad.config(text=producto[7])  # unidad_display
            except Exception:
                self.label_unidad.config(text="")

    def registrar_autoconsumo(self):
        """Registra un autoconsumo"""
        selected = self.combo_producto.get()
        cantidad_str = self.entry_cantidad.get().strip()
        motivo = self.entry_motivo.get().strip()
        
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un producto.")
            return
            
        if not cantidad_str:
            messagebox.showwarning("Advertencia", "Ingrese la cantidad.")
            return
            
        try:
            producto_id = int(selected.split(" - ")[0])
            cantidad = Decimal(cantidad_str)
            
            if cantidad <= Decimal('0'):
                raise ValueError("La cantidad debe ser un número positivo.")
                
            # Registrar autoconsumo
            self.autoconsumo_manager.registrar_autoconsumo(producto_id, cantidad, "", motivo)
            
            messagebox.showinfo("Éxito", "Autoconsumo registrado correctamente.")
            
            # Limpiar campos
            self.entry_cantidad.delete(0, tk.END)
            self.entry_motivo.delete(0, tk.END)
            
            # Actualizar historial
            self.load_historial_autoconsumo()
            
        except InvalidOperation:
            messagebox.showerror("Error", "Ingrese una cantidad válida.")
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el autoconsumo: {str(e)}")

    def load_historial_autoconsumo(self):
        """Carga el historial de autoconsumo"""
        # Limpiar treeview
        for item in self.tree_historial.get_children():
            self.tree_historial.delete(item)
            
        try:
            historial = self.autoconsumo_manager.obtener_historial_autoconsumo()
            
            for entry in historial:
                self.tree_historial.insert("", "end", values=(
                    entry['id'],
                    entry['nombre_producto'],
                    f"{entry['cantidad']:.4f}",
                    entry['unidad'],
                    entry['motivo'] if entry['motivo'] else "N/A",
                    entry['fecha_autoconsumo'].strftime('%Y-%m-%d %H:%M'),
                    f"{entry['costo']:.2f}"
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el historial: {str(e)}")
