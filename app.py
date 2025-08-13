import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from Core.database import Database
from Core.productos import Productos
from Core.compras import Compras
from Core.produccion import Produccion
from Core.recetas import RecetasManager
from Core.ventas import Ventas
from Core.clientes import Clientes
from Core.autoconsumo import Autoconsumo
from Core.cache_manager import cache_manager
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class App:
    """Enhanced Business Management Application with caching and better control"""
    
    def __init__(self, root):
        self.root = root
        self.db = Database()
        self.cache = cache_manager
        
        # Application state
        self.current_page = None
        self.managers = {}
        self.pages = {}
        
        # Setup
        self._setup_logging()
        self._setup_styles()
        self._initialize_managers()
        self._setup_ui()
        self._setup_protocols()
        
    def _setup_logging(self):
        """Configure application logging"""
        logger.info("Starting Business Management Application")
        
    def _setup_styles(self):
        """Configure application styles"""
        configure_styles()
        logger.info("Styles configured successfully")
        
    def _initialize_managers(self):
        """Initialize all business managers with caching support"""
        try:
            self.managers = {
                'productos': Productos(self.db),
                'compras': Compras(self.db, self.managers.get('productos')),
                'produccion': Produccion(self.db),
                'recetas': RecetasManager(self.db),
                'ventas': Ventas(self.db),
                'clientes': Clientes(self.db),
                'autoconsumo': Autoconsumo(self.db)
            }
            logger.info("All managers initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize managers: {e}")
            messagebox.showerror("Error de Inicialización", f"No se pudieron inicializar los módulos: {str(e)}")
            self.root.destroy()
            
    def _setup_ui(self):
        """Setup enhanced user interface"""
        self.root.title("Sistema de Gestión Comercial - Enhanced")
        self.root.geometry("1400x800")
        self.root.minsize(1200, 700)
        
        # Configure grid weights for responsive design
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        
        # Setup responsive grid
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)  # Content area
        
        # Create UI components
        self._create_sidebar()
        self._create_content_area()
        self._create_status_bar()
        
        # Show default page
        self.show_gestion_productos()
        
    def _create_sidebar(self):
        """Create enhanced sidebar with icons and better UX"""
        self.sidebar = ttk.Frame(self.main_container, width=250)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Sidebar title
        title_label = ttk.Label(
            self.sidebar,
            text="Gestión Comercial",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10)
        
        # Navigation buttons with icons
        nav_buttons = [
            ("📦 Productos", "gestion_productos", self.show_gestion_productos),
            ("🛒 Compras", "gestion_compras", self.show_gestion_compras),
            ("🏭 Producción", "gestion_produccion", self.show_gestion_produccion),
            ("📋 Recetas", "gestion_recetas", self.show_gestion_recetas),
            ("💰 Ventas", "gestion_ventas", self.show_gestion_ventas),
            ("👥 Clientes", "gestion_clientes", self.show_gestion_clientes),
            ("🏠 Autoconsumo", "gestion_autoconsumo", self.show_gestion_autoconsumo),
            ("💳 Flujo de Caja", "cash_flow", self.show_cash_flow),
            ("📊 Resumen Ventas", "resumen_ventas", self.show_resumen_ventas),
            ("❌ Salir", "exit", self.exit_application)
        ]
        
        for text, page_name, command in nav_buttons:
            btn = ttk.Button(
                self.sidebar,
                text=text,
                command=lambda cmd=command: self._safe_navigate(cmd),
                style="Sidebar.TButton",
                width=25
            )
            btn.pack(pady=3, padx=5, fill=tk.X)
            
    def _create_content_area(self):
        """Create main content area"""
        self.content_area = ttk.Frame(self.main_container)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Configure content area grid
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
    def _create_status_bar(self):
        """Create status bar with system information"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        
        # Status labels
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.db_status_label = ttk.Label(self.status_bar, text="DB: Connected")
        self.db_status_label.pack(side=tk.RIGHT, padx=5)
        
    def _safe_navigate(self, command):
        """Safe navigation with error handling"""
        try:
            command()
            self._update_status(f"Navigated to {command.__name__}")
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            messagebox.showerror("Navigation Error", str(e))
            
    def _update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
        logger.info(message)
        
    def _clear_content_area(self):
        """Clear content area safely"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
            
    def _show_page(self, page_class, manager_key=None, *additional_args):
        """Generic method to show pages with caching"""
        self._clear_content_area()
        
        try:
            manager = self.managers.get(manager_key) if manager_key else None
            args = [self.content_area]
            
            if manager:
                args.append(manager)
            args.extend(additional_args)
            
            page = page_class(*args)
            page.grid(row=0, column=0, sticky="nsew")
            
            self.current_page = page
            logger.info(f"Loaded page: {page_class.__name__}")
            
        except Exception as e:
            logger.error(f"Error loading page {page_class.__name__}: {e}")
            messagebox.showerror("Error", f"Error loading page: {str(e)}")
            
    def show_gestion_productos(self):
        """Show products management page"""
        self._show_page(GestionProductos, 'productos')
        
    def show_gestion_compras(self):
        """Show purchases management page"""
        self._show_page(GestionCompras, 'compras', self.managers['productos'])
        
    def show_gestion_produccion(self):
        """Show production management page"""
        self._show_page(GestionProduccion, 'produccion', self.managers['productos'])
        
    def show_gestion_recetas(self):
        """Show recipes management page"""
        self._show_page(RecetasEditor, 'recetas', self.managers['productos'])
        
    def show_gestion_ventas(self):
        """Show sales management page"""
        self._show_page(GestionVentas, 'ventas', self.managers['productos'], self.managers['recetas'])
        
    def show_gestion_clientes(self):
        """Show clients management page"""
        self._show_page(GestionClientes, 'clientes')
        
    def show_gestion_autoconsumo(self):
        """Show autoconsumo management page"""
        self._show_page(GestionAutoconsumo, 'autoconsumo', self.managers['productos'])
        
    def show_cash_flow(self):
        """Show cash flow page"""
        if 'reportes' not in self.managers:
            from Core.reportes import Reportes
            self.managers['reportes'] = Reportes(self.db)
            
        self._show_page(CashFlowPage, None, self.managers['reportes'], self.managers['ventas'], self.managers['productos'], self.managers['autoconsumo'])
        
    def show_resumen_ventas(self):
        """Show sales summary page"""
        if 'reportes' not in self.managers:
            from Core.reportes import Reportes
            self.managers['reportes'] = Reportes(self.db)
            
        self._show_page(ResumenVentasPage, None, self.managers['reportes'], self.managers['recetas'], self.managers['ventas'])
        
    def _setup_protocols(self):
        """Setup application protocols"""
        self.root.protocol("WM_DELETE_WINDOW", self.exit_application)
        
    def exit_application(self):
        """Enhanced exit with proper cleanup"""
        if messagebox.askyesno("Salir", "¿Está seguro de que desea salir de la aplicación?"):
            try:
                # Clear cache
                self.cache.clear_pattern("*")
                
                # Close database connection
                self.db.close_connection()
                logger.info("Application shutdown complete")
                
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
                
            self.root.destroy()

def main():
    """Main application entry point"""
    try:
        root = tk.Tk()
        app = App(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Application startup error: {e}")
        messagebox.showerror("Startup Error", f"Error starting application: {str(e)}")

if __name__ == "__main__":
    main()
