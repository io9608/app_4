# app.py
#bin/python3.11
import tkinter as tk
from tkinter import ttk, messagebox
from Core.database import Database
from Core.productos import Productos
from Core.compras import Compras
from Core.produccion import Produccion
from Core.recetas import RecetasManager
from Core.ventas import Ventas
from Core.clientes import Clientes
from Core.autoconsumo import Autoconsumo
from Gui.pages.gestion_productos_page import GestionProductos
from Gui.pages.gestion_compras_page import GestionCompras
from Gui.pages.gestion_produccion_page import GestionProduccion
from Gui.pages.gestion_recetas_page import RecetasEditor
from Gui.pages.gestion_ventas_page import GestionVentas
from Gui.pages.gestion_clientes_page import GestionClientes
from Gui.pages.gestion_autoconsumo_page import GestionAutoconsumo
from Gui.pages.cash_flow_page import CashFlowPage
from Gui.pages.resumen_ventas_page import ResumenVentasPage
from Gui.styles import configure_styles

class App:
    def __init__(self, root):
        self.root = root
        self.db = Database()

        # Configurar estilos antes de crear cualquier widget
        configure_styles()

        # CAMBIO CLAVE: Inicializar managers ANTES de configurar la UI
        self._initialize_managers()

        self._setup_ui()

        # Añadir el protocolo para cerrar la conexión al cerrar la ventana
        self.root.protocol("WM_DELETE_WINDOW", self.exit_application)

    def _setup_ui(self):
        """Configura la interfaz de usuario principal."""
        self.root.title("Sistema de Gestión Comercial")
        self.root.geometry("1200x700")

        # Frame principal
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        self.sidebar = ttk.Frame(self.main_frame, width=200, style="Sidebar.TFrame")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Content area
        self.content_area = ttk.Frame(self.main_frame, style="TFrame")
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Configurar sidebar
        self._setup_sidebar()

        # Mostrar la página de gestión de productos por defecto
        self.show_gestion_productos()

    def _initialize_managers(self):
        """Inicializa todas las clases de gestión (managers)"""
        try:
            self.productos_manager = Productos(self.db)
            self.compras_manager = Compras(self.db, self.productos_manager)
            self.produccion_manager = Produccion(self.db)
            self.recetas_manager = RecetasManager(self.db)
            self.ventas_manager = Ventas(self.db)
            self.clientes_manager = Clientes(self.db)
            self.autoconsumo_manager = Autoconsumo(self.db)

        except Exception as e:
            messagebox.showerror("Error de Inicialización", f"No se pudieron inicializar los módulos: {str(e)}")
            self.root.destroy()

    def _setup_sidebar(self):
        """Configura los botones de navegación en la sidebar."""
        buttons = [
            ("Gestión de Productos", self.show_gestion_productos),
            ("Registro de Compras", self.show_gestion_compras),
            ("Producción", self.show_gestion_produccion),
            ("Gestión de Recetas", self.show_gestion_recetas),
            ("Registro de Ventas", self.show_gestion_ventas),
            ("Autoconsumo", self.show_gestion_autoconsumo),
            ("Flujo de Caja", self.show_cash_flow),
            ("Resumen de Ventas", self.show_resumen_ventas),
            ("Clientes", self.show_gestion_clientes),
            ("Salir", self.exit_application) # Nuevo botón de salir
        ]

        for text, command in buttons:
            btn = ttk.Button(
                self.sidebar,
                text=text,
                command=command,
                style="Sidebar.TButton",
                width=20
            )
            btn.pack(pady=5, padx=5, fill=tk.X)

    # Métodos para mostrar cada página (simplificados sin controles de inicialización redundantes)
    def show_gestion_productos(self):
        """Muestra la página de gestión de productos."""
        self._clear_content_area()
        self.gestion_productos_page_instance = GestionProductos(
            self.content_area,
            self.productos_manager
        )
        self.gestion_productos_page_instance.pack(fill=tk.BOTH, expand=True)

    def show_gestion_compras(self):
        """Muestra la página de gestión de compras."""
        self._clear_content_area()
        self.gestion_compras_page_instance = GestionCompras(
            self.content_area,
            self.compras_manager,
            self.productos_manager,
            self.show_gestion_productos  # Callback para actualizar productos
        )
        self.gestion_compras_page_instance.pack(fill=tk.BOTH, expand=True)

    def show_gestion_produccion(self):
        """Muestra la página de gestión de producción."""
        self._clear_content_area()
        self.gestion_produccion_page_instance = GestionProduccion(
            self.content_area,
            self.produccion_manager,
            self.productos_manager
        )
        self.gestion_produccion_page_instance.pack(fill=tk.BOTH, expand=True)

    def show_gestion_recetas(self):
        """Muestra la página de gestión de recetas."""
        self._clear_content_area()
        self.gestion_recetas_page_instance = RecetasEditor(
            self.content_area,
            self.productos_manager,
            self.recetas_manager
        )
        self.gestion_recetas_page_instance.pack(fill=tk.BOTH, expand=True)

    def show_gestion_ventas(self):
        """Muestra la página de gestión de ventas."""
        self._clear_content_area()
        self.gestion_ventas_page_instance = GestionVentas(
            self.content_area,
            self.ventas_manager,
            self.productos_manager,
            self.recetas_manager
        )
        self.gestion_ventas_page_instance.pack(fill=tk.BOTH, expand=True)

    def show_gestion_clientes(self):
        """Muestra la página de gestión de clientes."""
        self._clear_content_area()
        self.gestion_clientes_page_instance = GestionClientes(
            self.content_area,
            self.clientes_manager
        )
        self.gestion_clientes_page_instance.pack(fill=tk.BOTH, expand=True)

    def show_gestion_autoconsumo(self):
        """Muestra la página de gestión de autoconsumo."""
        self._clear_content_area()
        self.gestion_autoconsumo_page_instance = GestionAutoconsumo(
            self.content_area,
            self.autoconsumo_manager,
            self.productos_manager
        )
        self.gestion_autoconsumo_page_instance.pack(fill=tk.BOTH, expand=True)

    def show_cash_flow(self):
        """Muestra la página de flujo de caja."""
        self._clear_content_area()
        # Inicializar el Reportes manager si no existe
        if not hasattr(self, 'reportes_manager'):
            from Core.reportes import Reportes
            self.reportes_manager = Reportes(self.db)

        self.cash_flow_page_instance = CashFlowPage(
            self.content_area,
            self.reportes_manager,
            self.ventas_manager,
            self.productos_manager,
            self.autoconsumo_manager
        )
        self.cash_flow_page_instance.pack(fill=tk.BOTH, expand=True)

    def show_resumen_ventas(self):
        """Muestra la página de resumen de ventas."""
        self._clear_content_area()
        # Inicializar el Reportes manager si no existe
        if not hasattr(self, 'reportes_manager'):
            from Core.reportes import Reportes
            self.reportes_manager = Reportes(self.db)

        self.resumen_ventas_page_instance = ResumenVentasPage(
            self.content_area,
            self.reportes_manager,
            self.recetas_manager,
            self.ventas_manager
        )
        self.resumen_ventas_page_instance.pack(fill=tk.BOTH, expand=True)

    def _clear_content_area(self):
        """Limpia el área de contenido antes de mostrar una nueva página."""
        for widget in self.content_area.winfo_children():
            widget.destroy()

    def exit_application(self):
        """Cierra la aplicación y la conexión a la base de datos."""
        if messagebox.askyesno("Salir", "¿Está seguro de que desea salir de la aplicación?"):
            try:
                self.db.close_connection() # Cerrar la conexión a la base de datos
                print("Conexión a la base de datos cerrada.")
            except Exception as e:
                print(f"Error al cerrar la conexión a la base de datos: {e}")
            self.root.destroy() # Destruir la ventana principal de Tkinter

# Inicialización de la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
