import tkinter.ttk as ttk
import tkinter as tk

def configure_styles():
    """Configura y aplica los estilos personalizados para la aplicación."""
    style = ttk.Style()

    # Paleta de colores profesional (azul corporativo + grises/naranjas)
    colores = {
        "primary": "#1E88E5",   # Azul principal
        "secondary": "#90CAF9",  # Azul claro
        "background": "#F5F5F5", # Fondo general de la aplicación
        "text": "#212121",      # Texto oscuro
        "accent": "#FF5722",    # Naranja para acciones destacadas (ej. Registrar)
        "white": "#FFFFFF",     # Blanco
        "light_gray": "#E0E0E0", # Gris claro para bordes/separadores
        "medium_gray": "#B0B0B0", # Gris medio para texto secundario
        "dark_sidebar": "#2C3E50", # Gris oscuro azulado para sidebar
        "active_sidebar": "#34495E", # Un poco más claro para hover/activo en sidebar
        "success": "#4CAF50",   # Verde para éxito
        "error": "#F44336",     # Rojo para error
        "warning": "#FFC107",   # Amarillo para advertencia
        "card_background": "#FFFFFF", # Fondo para tarjetas
        "card_border": "#DDDDDD", # Borde para tarjetas
        "highlight": "#FFD54F", # Amarillo para resaltar
    }

    # Configuración de fuentes base
    style.configure(".", font=("Segoe UI", 10)) # Fuente por defecto para todos los widgets

    # Estilo para Frames
    style.configure("TFrame", background=colores["background"])
    style.configure("Card.TFrame",
                    background=colores["card_background"],
                    borderwidth=1,
                    relief="flat", # Cambiado a flat para un look más moderno
                    bordercolor=colores["card_border"],
                    padding=15) 
    style.configure("Sidebar.TFrame", background=colores["dark_sidebar"])

    # Estilo para Labels
    style.configure("TLabel",
                    background=colores["background"],
                    foreground=colores["text"])

    # Estilo para Títulos
    style.configure("Titulo.TLabel",
                    font=("Segoe UI", 18, "bold"), # Aumentado tamaño
                    foreground=colores["primary"],
                    background=colores["background"])

    # Estilo para Subtítulos
    style.configure("Subtitulo.TLabel",
                    font=("Segoe UI", 12, "bold"),
                    foreground=colores["text"],
                    background=colores["background"])

    # Estilo para LabelFrames
    style.configure("TLabelframe",
                    background=colores["background"],
                    foreground=colores["text"],
                    font=("Segoe UI", 11, "bold"))
    style.configure("TLabelframe.Label",
                    background=colores["background"],
                    foreground=colores["text"],
                    font=("Segoe UI", 11, "bold"))

    # Estilo para Botones (Modern.TButton)
    style.configure("Modern.TButton",
                    font=("Segoe UI", 10, "bold"),
                    borderwidth=0,
                    padding=(10, 5), # Aumentado padding
                    relief="flat",
                    background=colores["primary"],
                    foreground=colores["white"])
    style.map("Modern.TButton",
              foreground=[('active', colores["white"]), ('!disabled', colores["white"])],
              background=[('active', '#1565C0'), ('!disabled', colores["primary"])]) # Darker on hover

    # Estilo para Botones de Acento (Accent.TButton) - para acciones principales
    style.configure("Accent.TButton",
                    font=("Segoe UI", 10, "bold"),
                    borderwidth=0,
                    padding=(10, 5),
                    relief="flat",
                    background=colores["accent"],
                    foreground=colores["white"])
    style.map("Accent.TButton",
              foreground=[('active', colores["white"]), ('!disabled', colores["white"])],
              background=[('active', '#E64A19'), ('!disabled', colores["accent"])])

    # Estilo para Entries (Modern.TEntry)
    style.configure("Modern.TEntry",
                    fieldbackground=colores["white"],
                    bordercolor=colores["light_gray"], # Borde más sutil
                    lightcolor=colores["light_gray"],
                    darkcolor=colores["light_gray"],
                    padding=5)
    style.map("Modern.TEntry",
              fieldbackground=[('readonly', colores["background"])]) # Fondo para readonly

    # Estilo para Combobox (Modern.TCombobox)
    style.configure("Modern.TCombobox",
                    fieldbackground=colores["white"],
                    bordercolor=colores["light_gray"],
                    lightcolor=colores["light_gray"],
                    darkcolor=colores["light_gray"],
                    padding=5)
    style.map("Modern.TCombobox",
              fieldbackground=[('readonly', colores["white"])],
              selectbackground=[('readonly', colores["primary"])],
              selectforeground=[('readonly', colores["white"])])

    # Estilo para Treeview (Modern.Treeview)
    style.configure("Modern.Treeview",
                    background=colores["white"],
                    foreground=colores["text"],
                    rowheight=28, # Aumentado altura de fila
                    fieldbackground=colores["white"],
                    font=('Segoe UI', 9))
    style.configure("Modern.Treeview.Heading",
                    font=('Segoe UI', 10, 'bold'),
                    background=colores["primary"],
                    foreground=colores["white"],
                    relief="flat",
                    padding=(0, 5)) # Padding en encabezados
    style.map("Modern.Treeview.Heading",
              background=[('active', '#1565C0')])
    style.map("Modern.Treeview",
              background=[('selected', colores["secondary"])],
              foreground=[('selected', colores["white"])])

    # Añadir un estilo Custom.Treeview que herede de Modern.Treeview (para consistencia)
    style.configure("Custom.Treeview",
                    background=colores["white"],
                    foreground=colores["text"],
                    rowheight=28,
                    fieldbackground=colores["white"],
                    font=('Segoe UI', 9))
    style.map("Custom.Treeview",
              background=[('selected', colores["secondary"])],
              foreground=[('selected', colores["white"])])
    style.configure("Custom.Treeview.Heading",
                    font=('Segoe UI', 10, 'bold'),
                    background=colores["primary"],
                    foreground=colores["white"],
                    relief="flat",
                    padding=(0, 5))
    style.map("Custom.Treeview.Heading",
              background=[('active', '#1565C0')])

    # Estilo para Notebook (pestañas)
    style.configure("TNotebook",
                    background=colores["background"],
                    borderwidth=0)
    style.configure("TNotebook.Tab",
                    background=colores["light_gray"], # Pestañas inactivas
                    foreground=colores["text"],
                    padding=(15, 8), # Aumentado padding
                    font=("Segoe UI", 10, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", colores["primary"])],
              foreground=[("selected", colores["white"])],
              expand=[("selected", (1, 1, 1, 0))])

    # Estilo para Radiobuttons y Checkbuttons
    style.configure("TRadiobutton",
                    background=colores["background"],
                    foreground=colores["text"],
                    font=("Segoe UI", 10))
    style.configure("TCheckbutton",
                    background=colores["background"],
                    foreground=colores["text"],
                    font=("Segoe UI", 10))

    # Estilo para Scrollbars
    style.configure("Vertical.TScrollbar",
                    background=colores["light_gray"],
                    troughcolor=colores["background"],
                    bordercolor=colores["light_gray"],
                    arrowcolor=colores["text"])
    style.map("Vertical.TScrollbar",
              background=[('active', colores["medium_gray"])])
              
    style.configure("Horizontal.TScrollbar",
                    background=colores["light_gray"],
                    troughcolor=colores["background"],
                    bordercolor=colores["light_gray"],
                    arrowcolor=colores["text"])
    style.map("Horizontal.TScrollbar",
              background=[('active', colores["medium_gray"])])

    # Estilo para el sidebar (botones del menú principal)
    style.configure("Sidebar.TButton",
                    font=("Segoe UI", 10, "bold"),
                    background=colores["dark_sidebar"],
                    foreground=colores["white"],
                    borderwidth=0,
                    padding=(20, 15),
                    relief="flat",
                    anchor="w")
    style.map("Sidebar.TButton",
              background=[('active', colores["active_sidebar"])],
              foreground=[('active', colores["white"])])

    # Estilo para mensajes de éxito/error/advertencia (opcional, si se usan labels específicos)
    style.configure("Success.TLabel", foreground=colores["success"], background=colores["background"], font=("Segoe UI", 10, "bold"))
    style.configure("Error.TLabel", foreground=colores["error"], background=colores["background"], font=("Segoe UI", 10, "bold"))
    style.configure("Warning.TLabel", foreground=colores["warning"], background=colores["background"], font=("Segoe UI", 10, "bold"))

    # Estilos adicionales para una mejor apariencia
    style.configure("Highlight.TLabel", 
                    background=colores["highlight"], 
                    foreground=colores["text"],
                    font=("Segoe UI", 10, "bold"),
                    padding=5)
                    
    style.configure("Info.TLabel", 
                    background=colores["background"], 
                    foreground=colores["medium_gray"],
                    font=("Segoe UI", 9))
                    
    # Estilo para botones pequeños (para acciones como eliminar, editar)
    style.configure("Small.TButton",
                    font=("Segoe UI", 9),
                    borderwidth=1,
                    padding=(5, 2),
                    relief="flat",
                    background=colores["light_gray"],
                    foreground=colores["text"])
    style.map("Small.TButton",
              foreground=[('active', colores["text"]), ('!disabled', colores["text"])],
              background=[('active', colores["medium_gray"]), ('!disabled', colores["light_gray"])])

