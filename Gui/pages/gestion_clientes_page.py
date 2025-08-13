import tkinter as tk
from tkinter import messagebox, ttk
from Core.clientes import Clientes

class GestionClientes(tk.Frame):
    def __init__(self, parent, clientes_manager):
        super().__init__(parent)
        self.clientes_manager = clientes_manager
        self.create_widgets()

    def create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        # Frame principal
        main_frame = tk.Frame(self, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # Título
        tk.Label(
            main_frame, 
            text="Gestión de Clientes",
            font=("Helvetica", 16, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")

        # Nombre del cliente
        tk.Label(main_frame, text="Nombre del Cliente:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_nombre_cliente = ttk.Entry(main_frame, width=30, style="Modern.TEntry") # Aplicar estilo
        self.entry_nombre_cliente.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Contacto del cliente
        tk.Label(main_frame, text="Contacto:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_contacto_cliente = ttk.Entry(main_frame, width=30, style="Modern.TEntry") # Aplicar estilo
        self.entry_contacto_cliente.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        # Teléfono del cliente
        tk.Label(main_frame, text="Teléfono:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_telefono_cliente = ttk.Entry(main_frame, width=30, style="Modern.TEntry") # Aplicar estilo
        self.entry_telefono_cliente.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        # Dirección del cliente
        tk.Label(main_frame, text="Dirección:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.entry_direccion_cliente = ttk.Entry(main_frame, width=30, style="Modern.TEntry") # Aplicar estilo
        self.entry_direccion_cliente.grid(row=4, column=1, sticky="ew", padx=5, pady=5)

        # Notas del cliente
        tk.Label(main_frame, text="Notas:").grid(row=5, column=0, sticky="ne", padx=5, pady=5)
        self.text_notas_cliente = tk.Text(main_frame, height=4, width=30)
        self.text_notas_cliente.grid(row=5, column=1, sticky="ew", padx=5, pady=5)

        # Botón para agregar cliente
        btn_agregar_cliente = ttk.Button(main_frame, text="Agregar Cliente", command=self.agregar_cliente, style="Accent.TButton") # Aplicar estilo
        btn_agregar_cliente.grid(row=6, columnspan=2, pady=(10, 0))

        # Tabla de clientes
        self.tree_clientes = ttk.Treeview(main_frame, columns=("ID", "Nombre", "Contacto", "Teléfono", "Dirección", "Notas"), show='headings', style="Modern.Treeview") # Aplicar estilo
        self.tree_clientes.heading("ID", text="ID")
        self.tree_clientes.heading("Nombre", text="Nombre")
        self.tree_clientes.heading("Contacto", text="Contacto")
        self.tree_clientes.heading("Teléfono", text="Teléfono")
        self.tree_clientes.heading("Dirección", text="Dirección")
        self.tree_clientes.heading("Notas", text="Notas")
        self.tree_clientes.grid(row=7, column=0, columnspan=2, pady=(10, 0), sticky="nsew")

        # Scrollbar para la tabla de clientes
        clientes_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree_clientes.yview, style="Vertical.TScrollbar")
        self.tree_clientes.configure(yscrollcommand=clientes_scrollbar.set)
        clientes_scrollbar.grid(row=7, column=2, sticky="ns")

        # Botón para cargar clientes
        btn_cargar_clientes = ttk.Button(main_frame, text="Cargar Clientes", command=self.cargar_clientes, style="Modern.TButton") # Aplicar estilo
        btn_cargar_clientes.grid(row=8, columnspan=2, pady=(10, 0))

        # Configurar expansión
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(7, weight=1) # Treeview de clientes

    def agregar_cliente(self):
        """Recoge los datos del formulario y agrega un nuevo cliente"""
        nombre_cliente = self.entry_nombre_cliente.get().strip()
        contacto_cliente = self.entry_contacto_cliente.get().strip()
        telefono_cliente = self.entry_telefono_cliente.get().strip()
        direccion_cliente = self.entry_direccion_cliente.get().strip()
        notas_cliente = self.text_notas_cliente.get("1.0", tk.END).strip()

        if not nombre_cliente:
            messagebox.showerror("Error", "El nombre del cliente es requerido.")
            return

        if not contacto_cliente:
            messagebox.showerror("Error", "El contacto del cliente es requerido.")
            return

        try:
            cliente_id = self.clientes_manager.agregar_cliente(nombre_cliente, contacto_cliente, telefono_cliente, direccion_cliente, notas_cliente)
            messagebox.showinfo("Éxito", f"Cliente agregado con ID: {cliente_id}")
            self.entry_nombre_cliente.delete(0, tk.END)
            self.entry_contacto_cliente.delete(0, tk.END)
            self.entry_telefono_cliente.delete(0, tk.END)
            self.entry_direccion_cliente.delete(0, tk.END)
            self.text_notas_cliente.delete("1.0", tk.END)
            self.cargar_clientes()  # Recargar la lista de clientes
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar el cliente: {str(e)}")

    def cargar_clientes(self):
        """Carga la lista de clientes en la tabla"""
        for row in self.tree_clientes.get_children():
            self.tree_clientes.delete(row)

        try:
            clientes = self.clientes_manager.obtener_todos_clientes()
            for cliente in clientes:
                self.tree_clientes.insert("", "end", values=(
                    cliente['id'],
                    cliente['nombre'],
                    cliente['contacto'],
                    cliente['telefono'],
                    cliente['direccion'],
                    cliente['notas']
                ))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los clientes: {str(e)}")
